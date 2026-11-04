#!/usr/bin/env python3
"""Validate installable plugin packages and build reproducible release archives."""
import argparse
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from urllib.request import urlopen
import zipfile

from jsonschema import Draft202012Validator
import yaml

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = re.compile(r"references/([a-z0-9_-]+\.md)")
SIBLING_REFERENCE = re.compile(r"(?<![\w/.-])([a-z][a-z0-9_-]*\.md)\b")
SKILLS = {
    "ace-capabilities", "ace-conversation-briefs", "ace-business-insights",
    "ace-team-performance", "ace-voice-of-customer", "ace-deals-intelligence",
}
CATALOGS = (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json")
SCHEMA_REVISION = "ff8ab5e392cc87bd88d87c060815a87490e51003"
SCHEMA_SHA256 = {
    "plugin": "0a4aad95ce337878ad38802ebf0daa3fde76abe3f65400c86bcbb1ec0b3ab883",
    "mcp": "6539175bfcdf43085855183e86da40ea94b166547a72b47ae9a0a390516d3acb",
}


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def safe_path(root, relative):
    """Contain every read/write and reject symlink components before following them."""
    rel = PurePosixPath(relative)
    require(not rel.is_absolute() and ".." not in rel.parts, f"Path must be contained: {relative}")
    current = root
    for part in rel.parts:
        current = current / part
        require(not current.is_symlink(), f"Symlink is not allowed: {relative}")
    require(current.resolve().is_relative_to(root.resolve()), f"Path must be contained: {relative}")
    return current


def read(root, relative):
    file = safe_path(root, relative)
    require(file.is_file(), f"Missing file or reference: {relative}")
    return file.read_bytes()


def load(root, relative):
    return json.loads(read(root, relative))


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def inventory(root, relative):
    directory = safe_path(root, relative)
    require(directory.is_dir(), f"Missing directory: {relative}")
    result = {}
    for file in sorted(directory.rglob("*")):
        rel = file.relative_to(root).as_posix()
        safe_path(root, rel)
        if file.is_file():
            result[rel] = file.read_bytes()
    return result


@lru_cache(maxsize=2)
def validation_schema(name):
    """Fetch a fixed upstream schema into memory and reject unexpected content."""
    require(name in SCHEMA_SHA256, f"Unknown validation schema: {name}")
    url = ("https://raw.githubusercontent.com/agentplugins/agent-plugins-spec/"
           f"{SCHEMA_REVISION}/schemas/1.0.0/{name}.schema.json")
    try:
        with urlopen(url, timeout=15) as response:
            content = response.read(1024 * 1024 + 1)
    except OSError as error:
        raise Invalid(f"Cannot download {name} validation schema; check access to "
                      "raw.githubusercontent.com and retry. Validation was not skipped.") from error
    require(len(content) <= 1024 * 1024, f"{name} validation schema exceeds the size limit")
    require(hashlib.sha256(content).hexdigest() == SCHEMA_SHA256[name],
            f"{name} validation schema checksum mismatch; validation stopped")
    return json.loads(content)


def schema_check(data, name):
    schema = validation_schema(name)
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: str(e.path))
    require(not errors, f"{name} schema: " + "; ".join(e.message for e in errors[:5]))


def https_url(url, label):
    parsed = urlsplit(url)
    require(parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password,
            f"{label} must be an HTTPS URL without credentials")


def package_files(root, kind):
    """Validate the self-contained files that a client installs."""
    prefix = f"plugins/{kind}/"
    files = inventory(root, prefix)
    allowed = {prefix + name for name in ("README.md", "LICENSE", ".mcp.json")}
    manifests = (".claude-plugin/plugin.json",) if kind == "claude" else ("plugin.json", "mcp.json", ".codex-plugin/plugin.json")
    allowed.update(prefix + name for name in manifests)
    assets = inventory(root, prefix + "assets")
    require(assets and all(Path(path).suffix.lower() in {".svg", ".png", ".jpg", ".jpeg", ".webp"} for path in assets),
            f"Expected image assets in {prefix}")
    allowed.update(assets)
    skills = inventory(root, prefix + "skills")
    require({path[len(prefix):].split('/')[1] for path in skills} == SKILLS,
            f"Expected the six supported skills in {prefix}")
    shared = {}
    for name in sorted(SKILLS):
        folder = prefix + f"skills/{name}/"
        rel = folder + "SKILL.md"
        text = read(root, rel).decode()
        front = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
        require(front is not None, f"Missing skill frontmatter: {rel}")
        meta = yaml.safe_load(front.group(1))
        require(isinstance(meta, dict) and meta.get("name") == name, f"Skill identity mismatch: {rel}")
        require(isinstance(meta.get("description"), str) and meta["description"].strip(), f"Missing skill description: {rel}")
        allowed.add(rel)
        metadata_path = folder + "agents/openai.yaml"
        if metadata_path in skills:
            require(kind == "openai", f"Unexpected OpenAI metadata in {prefix}")
            data = yaml.safe_load(skills[metadata_path])
            interface = data.get("interface") if isinstance(data, dict) else None
            require(isinstance(interface, dict), f"Expected an interface mapping: {metadata_path}")
            for field in ("display_name", "short_description"):
                require(isinstance(interface.get(field), str) and interface[field].strip(), f"Missing {field}: {metadata_path}")
            allowed.add(metadata_path)
        pending = set(REFERENCE.findall(text))
        copied = set()
        while pending:
            ref = pending.pop()
            if ref in copied:
                continue
            path = folder + "references/" + ref
            data = read(root, path)
            require(ref not in shared or shared[ref] == data, f"Reference copies disagree: {ref}")
            shared[ref] = data
            allowed.add(path)
            copied.add(ref)
            pending.update((set(REFERENCE.findall(data.decode())) | set(SIBLING_REFERENCE.findall(data.decode()))) - copied)
    require(set(files) == allowed, f"Missing or unexpected package files: {', '.join(sorted(set(files) ^ allowed))}")
    return files


def check(root, tag=None, submission=False):
    manifest = load(root, "plugins/openai/plugin.json")
    schema_check(manifest, "plugin")
    require(manifest.get("name") == "ringcentral-ace", "Preserve the ringcentral-ace plugin identity")
    require(re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", manifest.get("version", "")),
            "Use a numeric x.y.z version without leading zeros")
    require(manifest.get("license") == "MIT" and b"MIT License" in read(root, "LICENSE"), "Package license must match MIT")
    require("extensions" not in manifest, "Use the standard portable identity and the supported Codex compatibility interface")
    compatibility = load(root, "plugins/openai/.codex-plugin/plugin.json")
    iface = compatibility.get("interface", {})
    for field, limit in (("displayName", 80), ("shortDescription", 30), ("longDescription", 4000)):
        value = iface.get(field)
        require(isinstance(value, str) and 0 < len(value) <= limit, f"interface.{field} must contain 1–{limit} characters")
    require(iface.get("category") == "Data & Analytics", "Use the Data & Analytics listing category")
    prompts = iface.get("defaultPrompt", [])
    require(isinstance(prompts, list) and 1 <= len(prompts) <= 3, "Provide one to three starter prompts")
    require(all(isinstance(p, str) and p.strip() and len(p) <= 128 and "\n" not in p for p in prompts),
            "Starter prompts must be single-line, at most 128 characters")
    require(len(set(p.strip() for p in prompts)) == len(prompts), "Starter prompts must be unique")
    for field in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        https_url(iface.get(field, ""), field)
    for field in ("logo", "logoDark", "composerIcon", "composerIconDark"):
        if field in iface:
            require(isinstance(iface[field], str) and iface[field].startswith("./assets/"), f"{field} must be contained in ./assets/")
            read(root, "plugins/openai/" + iface[field])
    common = {k: manifest[k] for k in ("name", "version", "description", "author", "homepage", "repository", "license", "keywords")}
    # Claude's Git sync importer strips directory-only listing fields.
    # Keep them in OpenAI metadata; the Claude Git package uses homepage and README links.
    claude = dict(common, displayName=iface["displayName"], mcpServers="./.mcp.json")
    compat = dict(common, displayName=iface["displayName"], skills="./skills/", mcpServers="./.mcp.json", interface=iface)
    require(load(root, "plugins/claude/.claude-plugin/plugin.json") == claude, "Claude manifest differs from the shared package metadata")
    require(compatibility == compat, "Codex compatibility manifest differs from the portable manifest")
    connection = load(root, "plugins/openai/mcp.json")
    require(set(connection) == {"$schema", "mcpServers"}, "Unexpected MCP configuration fields")
    require(set(connection.get("mcpServers", {})) == {"ringcentral-ace"}, "Preserve the ringcentral-ace MCP connector identity")
    server = connection["mcpServers"]["ringcentral-ace"]
    https_url(server.get("url", ""), "ringcentral-ace")
    require(server.get("type") == "streamable-http", "Use Streamable HTTP transport")
    schema_check(connection, "mcp")
    legacy = {"mcpServers": {"ringcentral-ace": {"type": "http", "url": server["url"], "oauth": {"callbackPort": 8080}}}}
    for kind in ("claude", "openai"):
        require(load(root, f"plugins/{kind}/.mcp.json") == legacy, f"MCP connection or OAuth settings disagree: {kind}")
    output = {}
    comparable = {}
    expected_readme = read(root, "README.md").decode().replace("](DEVELOPMENT.md)", f"]({manifest['repository']}/blob/main/DEVELOPMENT.md)").encode()
    for kind in ("claude", "openai"):
        prefix = f"plugins/{kind}/"
        files = package_files(root, kind)
        require(files[prefix + "LICENSE"] == read(root, "LICENSE"), f"License mismatch: {kind}")
        require(files[prefix + "README.md"] == expected_readme, f"Package README differs from the repository README: {kind}")
        comparable[kind] = {p[len(prefix):]: data for p, data in files.items()
                            if p[len(prefix):].startswith(("skills/", "assets/")) and not p.endswith("/agents/openai.yaml")}
        output.update(files)
    require(comparable["claude"] == comparable["openai"], "Packaged skills, references, or assets disagree across clients")
    catalogs = [load(root, rel) for rel in CATALOGS]
    market = catalogs[0]
    require(market.get("name") == "ringcentral-ace-conversation-intelligence", "Preserve the marketplace identity")
    require(isinstance(market.get("description"), str) and market["description"].strip(), "Marketplace description is required")
    require(isinstance(market.get("owner", {}).get("name"), str) and market["owner"]["name"].strip(), "Marketplace owner is required")
    for kind, rel, catalog in zip(("claude", "openai"), CATALOGS, catalogs):
        entry = {"name": manifest["name"], "source": f"./plugins/{kind}", "description": manifest["description"]}
        expected = {k: market[k] for k in ("name", "description", "owner")}
        expected["plugins"] = [entry]
        if kind == "openai":
            entry.update(source={"source": "local", "path": "./plugins/openai"},
                         policy={"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, category=iface["category"])
            expected["interface"] = {"displayName": iface["displayName"]}
        require(catalog == expected, f"Marketplace does not match the installed package: {rel}")
        output[rel] = read(root, rel)
    root_files = ("plugin-manifest.json", "mcp-manifest.json", "marketplace.json", "skills", "shared-references", "assets")
    # Older distribution-only tags remain valid for release recovery. When the
    # shared files are present, require a complete, aligned public source tree.
    if any(safe_path(root, rel).exists() for rel in root_files):
        require(all(safe_path(root, rel).exists() for rel in root_files), "Incomplete root plugin files")
        require(load(root, "plugin-manifest.json") == compat, "Root compatibility source differs from the package metadata")
        require(load(root, "mcp-manifest.json") == {"mcpServers": connection["mcpServers"], "claudeOAuth": {"callbackPort": 8080}},
                "Root MCP configuration differs from the packages")
        require(load(root, "marketplace.json") == {k: market[k] for k in ("name", "description", "owner")},
                "Root marketplace metadata differs from the catalogs")
        expected_skills = {p.removeprefix("plugins/openai/"): data for p, data in output.items()
                           if p.startswith("plugins/openai/skills/") and p.endswith(("/SKILL.md", "/agents/openai.yaml"))}
        require(inventory(root, "skills") == expected_skills, "Root skills differ from the packages")
        expected_assets = {p.removeprefix("plugins/openai/"): data for p, data in output.items()
                           if p.startswith("plugins/openai/assets/")}
        require(inventory(root, "assets") == expected_assets, "Root assets differ from the packages")
        expected_references = {"shared-references/" + Path(p).name: data for p, data in output.items()
                               if p.startswith("plugins/openai/skills/") and "/references/" in p}
        require(inventory(root, "shared-references") == expected_references, "Root references differ from the packages")
    if tag:
        require(tag == "v" + manifest["version"], "Release tag must match v" + manifest["version"])
    if submission:
        require(len(iface["displayName"]) <= 30, f"OpenAI public listing displayName is {len(iface['displayName'])} characters; limit is 30.")
    print(f"Package checks passed ({len(output)} packaged files).")
    return output


def set_version(root, version):
    """Update versioned package manifests after validating the complete checkout."""
    require(re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version), "Use a numeric x.y.z version")
    check(root)
    paths = ("plugins/openai/plugin.json", "plugins/openai/.codex-plugin/plugin.json", "plugins/claude/.claude-plugin/plugin.json")
    if safe_path(root, "plugin-manifest.json").exists():
        paths += ("plugin-manifest.json",)
    prepared = {}
    for rel in paths:
        manifest = load(root, rel)
        manifest["version"] = version
        prepared[rel] = json_bytes(manifest)
    for rel, data in prepared.items():
        atomic_write(safe_path(root, rel), data)


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
        temporary = Path(temp.name)
        temp.write(data)
    try:
        temporary.chmod(0o644)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build(root):
    expected = check(root)
    manifest = load(root, "plugins/openai/plugin.json")
    dist = safe_path(root, "dist")
    dist.mkdir(exist_ok=True)
    previous = inventory(root, "dist")
    archive_name = re.compile(re.escape(manifest["name"]) + r"-(?:claude|openai)-\d+\.\d+\.\d+\.zip")
    for relative in previous:
        name = relative.removeprefix("dist/")
        require(name == "SHA256SUMS" or archive_name.fullmatch(name), f"Unexpected file in dist; move it before building: {relative}")
    checksums = []
    keep = {"dist/SHA256SUMS"}
    for kind in ("claude", "openai"):
        name = f"{manifest['name']}-{kind}-{manifest['version']}.zip"
        keep.add("dist/" + name)
        output = safe_path(root, "dist/" + name)
        prefix = f"plugins/{kind}/"
        with tempfile.NamedTemporaryFile(dir=dist, delete=False) as temp:
            temporary = Path(temp.name)
        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for relative, content in sorted(expected.items()):
                    if not relative.startswith(prefix):
                        continue
                    member = relative[len(prefix):]
                    info = zipfile.ZipInfo(member, (2020, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, content, compresslevel=9)
            os.replace(temporary, output)
        finally:
            temporary.unlink(missing_ok=True)
        checksums.append(f"{hashlib.sha256(output.read_bytes()).hexdigest()}  {name}")
        print("Built dist/" + name)
    atomic_write(safe_path(root, "dist/SHA256SUMS"), ("\n".join(checksums) + "\n").encode())
    for relative in previous.keys() - keep:
        safe_path(root, relative).unlink()


def check_staged(root):
    """Validate the index in a temporary tree without staging or changing files."""
    with tempfile.TemporaryDirectory(prefix="rc-plugin-index-") as directory:
        snapshot = Path(directory)
        result = subprocess.run(
            ["git", "-C", str(root), "checkout-index", "--all", "--prefix", snapshot.as_posix() + "/"],
            capture_output=True, text=True,
        )
        require(result.returncode == 0, "Cannot inspect staged snapshot: " + result.stderr)
        check(snapshot)


def install_hooks(root):
    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    top = git("rev-parse", "--show-toplevel")
    require(top.returncode == 0 and Path(top.stdout.strip()).resolve() == root.resolve(), "Run from the repository checkout")
    existing = git("config", "--get", "core.hooksPath")
    require(not existing.stdout.strip() or existing.stdout.strip() == ".githooks", "Preserving existing core.hooksPath; integrate the check into your current hook instead")
    if not existing.stdout.strip():
        hooks = Path(git("rev-parse", "--git-path", "hooks").stdout.strip())
        if not hooks.is_absolute():
            hooks = root / hooks
        active = [p.name for p in hooks.glob("*") if p.is_file() and not p.name.endswith(".sample")]
        require(not active, "Preserving existing Git hooks: " + ", ".join(active))
    hook = safe_path(root, ".githooks/pre-commit")
    require(hook.is_file(), "Missing .githooks/pre-commit")
    hook.chmod(0o755)
    result = git("config", "--local", "core.hooksPath", ".githooks")
    require(result.returncode == 0, result.stderr)
    print("Enabled repository-local validation hook; no files were staged.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    subs = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "submission-check", "install-hooks", "check-staged"):
        subs.add_parser(command)
    subs.add_parser("check").add_argument("--tag", help="Require a matching release tag")
    args = parser.parse_args()
    try:
        if args.command == "check":
            check(args.root, tag=args.tag)
        elif args.command == "submission-check":
            check(args.root, submission=True)
        else:
            {"build": build, "install-hooks": install_hooks, "check-staged": check_staged}[args.command](args.root)
        return 0
    except (Invalid, OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

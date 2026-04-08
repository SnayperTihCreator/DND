import importlib.metadata
import subprocess

version_info = importlib.metadata.version("dnd")

tag = f"v{version_info.removeprefix('v')}"
subprocess.run(["git", "tag", "-d", tag], shell=True, stdout=subprocess.DEVNULL)
subprocess.run(["git", "tag", tag], shell=True)

subprocess.run(["git", "push", "--tag"], shell=True)
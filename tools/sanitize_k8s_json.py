import argparse
import json
import sys


def drop_keys(obj: dict, keys: list[str]) -> None:
    for key in keys:
        obj.pop(key, None)


def drop_nested(obj: dict, path: list[str]) -> None:
    cur = obj
    for key in path[:-1]:
        if not isinstance(cur, dict) or key not in cur:
            return
        cur = cur[key]
    if isinstance(cur, dict):
        cur.pop(path[-1], None)


EPHEMERAL_METADATA_KEYS = [
    "managedFields",
    "resourceVersion",
    "uid",
    "selfLink",
    "generation",
]


EPHEMERAL_ANNOTATIONS = {
    "kubectl.kubernetes.io/last-applied-configuration",
    "deployment.kubernetes.io/revision",
}


def sanitize_common(doc: dict) -> dict:
    if not isinstance(doc, dict):
        return doc

    doc.pop("status", None)

    metadata = doc.get("metadata")
    if isinstance(metadata, dict):
        drop_keys(metadata, EPHEMERAL_METADATA_KEYS)
        metadata.pop("creationTimestamp", None)

        annotations = metadata.get("annotations")
        if isinstance(annotations, dict):
            for k in list(annotations.keys()):
                if k in EPHEMERAL_ANNOTATIONS:
                    annotations.pop(k, None)
            if not annotations:
                metadata.pop("annotations", None)

    return doc


def sanitize_service(doc: dict) -> dict:
    spec = doc.get("spec")
    if isinstance(spec, dict):
        # Immutable / cluster-assigned fields that frequently break adoption
        for key in [
            "clusterIP",
            "clusterIPs",
            "ipFamilies",
            "ipFamilyPolicy",
            "internalTrafficPolicy",
            "healthCheckNodePort",
        ]:
            spec.pop(key, None)

        ports = spec.get("ports")
        if isinstance(ports, list):
            for port in ports:
                if isinstance(port, dict):
                    port.pop("nodePort", None)
    return doc


def sanitize_ingress(doc: dict) -> dict:
    # status already removed; keep spec
    return doc


def sanitize_workload(doc: dict) -> dict:
    # Remove pod-template ephemeral fields if present
    drop_nested(doc, ["spec", "template", "metadata", "creationTimestamp"])
    return doc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True)
    args = parser.parse_args()

    raw = sys.stdin.read()
    doc = json.loads(raw)

    kind = args.kind.lower()
    doc = sanitize_common(doc)

    if kind == "service":
        doc = sanitize_service(doc)
    elif kind == "ingress":
        doc = sanitize_ingress(doc)
    else:
        doc = sanitize_workload(doc)

    json.dump(doc, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

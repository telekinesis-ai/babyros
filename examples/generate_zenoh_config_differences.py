import zenoh
import json


def config_to_dict(config):
    try:
        return json.loads(config.to_json())
    except AttributeError:
        return json.loads(str(config))


def flatten_dict(d, parent_key="", sep="."):
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


def compare_table_md(d1, d2, filename="zenoh_config_differences.md"):
    flat1 = flatten_dict(d1)
    flat2 = flatten_dict(d2)

    all_keys = sorted(set(flat1) | set(flat2))

    lines = []
    lines.append("# Zenoh Config Differences Between Zenoh, BabyROS, and RMW Zenoh\n")
    lines.append("| Key | BabyROS | Zenoh | RMW Zenoh |")
    lines.append("|-----|--------|-----------|-----------|")

    for key in all_keys:
        v1 = flat1.get(key, "—")
        v2 = flat2.get(key, "—")

        if v1 != v2:
            # escape pipes to avoid breaking markdown table
            v1_str = str(v1).replace("|", "\\|")
            v2_str = str(v2).replace("|", "\\|")

            lines.append(f"| {key} | {v1_str} | {v1_str} | {v2_str} |")

    with open(filename, "w") as f:
        f.write("\n".join(lines))

    print(f"Markdown file generated: {filename}")


def load_config():
    return zenoh.Config.from_file("../config/DEFAULT_RMW_ZENOH_SESSION_CONFIG.json5")


if __name__ == "__main__":
    default_config = zenoh.Config()
    ros_config = load_config()

    d1 = config_to_dict(default_config)
    d2 = config_to_dict(ros_config)

    compare_table_md(d1, d2)

import matplotlib.pyplot as plt
import numpy as np

# # Data from the three cases
# cases = ["Case 1", "Case 2", "Case 3"]

# primary_physical = [5, 5, 5]
# backup_physical = [9, 9, 12]

# # Case 1 does not use topology aggregation
# primary_aggregated = [np.nan, 3, 3]
# backup_aggregated = [np.nan, 3, 3]

# x = np.arange(len(cases))
# width = 0.18

# plt.figure(figsize=(10, 6))

# plt.bar(x - 1.5 * width, primary_physical, width,
#         label="Primary physical path")

# plt.bar(x - 0.5 * width, backup_physical, width,
#         label="Backup physical path")

# plt.bar(x + 0.5 * width, primary_aggregated, width,
#         label="Primary aggregated path")

# plt.bar(x + 1.5 * width, backup_aggregated, width,
#         label="Backup aggregated path")

# plt.xlabel("Information-sharing scenario")
# plt.ylabel("Hop count")
# plt.title("Comparison of Path Lengths Across Information-Sharing Scenarios")

# plt.xticks(x, cases)
# plt.yticks(range(0, 14, 2))
# plt.ylim(0, 14)

# plt.legend()
# plt.grid(axis="y", linestyle="--", alpha=0.3)

# plt.tight_layout()
# plt.show()




import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(11, 6))

# Fixed color for each path type
colors = {
    "Primary physical": "red",
    "Backup physical": "blue",
    "Primary aggregated": "green",
    "Backup aggregated": "orange"
}

# Data from the simulations
cases = {
    "Case 1": [
        ("Primary physical", 5),
        ("Backup physical", 9)
    ],
    "Case 2": [
        ("Primary physical", 5),
        ("Backup physical", 9),
        ("Primary aggregated", 3),
        ("Backup aggregated", 3)
    ],
    "Case 3": [
        ("Primary physical", 5),
        ("Backup physical", 12),
        ("Primary aggregated", 3),
        ("Backup aggregated", 3)
    ]
}

case_positions = [2, 6, 10]

for i, (case_name, paths) in enumerate(cases.items()):

    center = case_positions[i]
    spacing = 0.6
    start = center - (len(paths) - 1) * spacing / 2

    for j, (path_name, hop_count) in enumerate(paths):

        x = start + j * spacing

        # Draw a colored vertical line
        ax.vlines(
            x, 0, hop_count,
            color=colors[path_name],
            linewidth=3
        )

        # Display hop count above each line
        ax.text(
            x, hop_count + 0.25,
            str(hop_count),
            ha="center",
            fontsize=10
        )

    # Horizontal line beneath each case
    ax.hlines(
        0, center - 1.3, center + 1.3,
        color="black",
        linewidth=1.5
    )

# Create legend (one entry per path type)
for path_name, color in colors.items():
    ax.plot([], [], color=color, linewidth=3, label=path_name)

ax.legend(loc="upper left", fontsize=12)

ax.set_xticks(case_positions)
ax.set_xticklabels(list(cases.keys()))

ax.set_xlabel("Information-sharing scenario")
ax.set_ylabel("Hop count")
ax.set_ylim(-0.5, 15)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()

# Save figure for LaTeX
plt.savefig("path_comparison.pdf", bbox_inches="tight")

plt.show()

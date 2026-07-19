import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# =====================================================
# DATASET
# =====================================================

data = {
    'Student':['A','B','C','D','E','F','G','H'],
    'Marks':[78,85,90,67,88,92,75,81],
    'Hours':[4,5,7,3,6,8,4,5],
    'Gender':['Male','Female','Male','Female',
              'Male','Female','Male','Female'],
    'Department':['CSE','ECE','CSE','EEE',
                  'ECE','CSE','EEE','ECE']
}

df = pd.DataFrame(data)

print(df)

# =====================================================
# FIGURE + AXES USING SUBPLOTS
# =====================================================

fig, ax = plt.subplots(2, 2, figsize=(12,8))

# =====================================================
# LINE PLOT
# =====================================================

ax[0,0].plot(
    df['Student'],
    df['Marks'],
    color='blue',
    marker='o',
    linestyle='--',
    label='Marks'
)

ax[0,0].set_title("Line Plot")
ax[0,0].set_xlabel("Students")
ax[0,0].set_ylabel("Marks")
ax[0,0].legend()
ax[0,0].grid(True)

# =====================================================
# SCATTER PLOT
# =====================================================

ax[0,1].scatter(
    df['Hours'],
    df['Marks'],
    color='red',
    marker='*'
)

ax[0,1].set_title("Scatter Plot")
ax[0,1].set_xlabel("Study Hours")
ax[0,1].set_ylabel("Marks")
ax[0,1].grid(True)

# =====================================================
# BAR PLOT
# =====================================================

ax[1,0].bar(
    df['Student'],
    df['Marks'],
    color='green'
)

ax[1,0].set_title("Bar Chart")
ax[1,0].set_xlabel("Student")
ax[1,0].set_ylabel("Marks")

# =====================================================
# HORIZONTAL BAR
# =====================================================

ax[1,1].barh(
    df['Student'],
    df['Marks'],
    color='orange'
)

ax[1,1].set_title("Horizontal Bar")

plt.tight_layout()
plt.show()

# =====================================================
# HISTOGRAM
# =====================================================

plt.figure(figsize=(6,4))

plt.hist(
    df['Marks'],
    bins=5,
    color='skyblue',
    edgecolor='black'
)

plt.title("Histogram")
plt.xlabel("Marks")
plt.ylabel("Frequency")
plt.grid(True)

plt.show()

# =====================================================
# PIE CHART
# =====================================================

dept_count = df['Department'].value_counts()

plt.figure(figsize=(6,6))

plt.pie(
    dept_count,
    labels=dept_count.index,
    autopct='%1.1f%%'
)

plt.title("Department Distribution")

plt.show()

# =====================================================
# BOXPLOT
# =====================================================

plt.figure(figsize=(6,4))

plt.boxplot(df['Marks'])

plt.title("Box Plot")
plt.ylabel("Marks")

plt.show()

# =====================================================
# FIG.ADD_SUBPLOT()
# =====================================================

fig = plt.figure(figsize=(10,4))

ax1 = fig.add_subplot(1,2,1)
ax2 = fig.add_subplot(1,2,2)

ax1.plot(df['Student'], df['Marks'])
ax1.set_title("add_subplot Line")

ax2.scatter(df['Hours'], df['Marks'])
ax2.set_title("add_subplot Scatter")

plt.tight_layout()
plt.show()

# =====================================================
# HEATMAP
# =====================================================

numeric_df = df[['Marks','Hours']]

corr = numeric_df.corr()

plt.figure(figsize=(6,4))

sns.heatmap(
    corr,
    annot=True,
    cmap='coolwarm'
)

plt.title("Heatmap")

plt.show()

# =====================================================
# PAIRPLOT
# =====================================================

sns.pairplot(
    df[['Marks','Hours']]
)

plt.show()

# =====================================================
# VIOLIN PLOT
# =====================================================

plt.figure(figsize=(6,4))

sns.violinplot(
    x='Gender',
    y='Marks',
    data=df
)

plt.title("Violin Plot")

plt.show()

# =====================================================
# CATPLOT
# =====================================================

sns.catplot(
    x='Department',
    y='Marks',
    kind='bar',
    data=df
)

plt.show()

# =====================================================
# SAVE FIGURE
# =====================================================

plt.figure(figsize=(6,4))

plt.plot(
    df['Student'],
    df['Marks'],
    marker='o'
)

plt.title("Saved Figure")

plt.savefig(
    "student_marks.png",
    dpi=300,
    bbox_inches='tight'
)

plt.show()

print("Figure Saved Successfully")
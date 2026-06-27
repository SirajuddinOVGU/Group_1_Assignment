# =========================
# 1. IMPORT PACKAGES
# =========================
import pandas as pd
from rapidfuzz import process, fuzz

# =========================
# 2. LOAD DATA FROM FILES
# =========================
# df_links = dataset with movie slugs / links (e.g. m/star_wars_episode...)
# df_titles = dataset with clean movie titles (e.g. Star Wars: The Force Awakens)

df_links = pd.read_excel("Outputs&ExcelFiles/MovieTitleMerging/links.xlsx")
df_titles = pd.read_excel("Outputs&ExcelFiles/MovieTitleMerging/titles.xlsx")

print("Links preview:")
print(df_links.head())

print("Titles preview:")
print(df_titles.head())

# =========================
# 3. CLEAN LINK DATA
# =========================
# Convert slug-style links into readable format:
# m/star_wars_episode_vii -> star wars episode vii

df_links['clean_link'] = (
    df_links.iloc[:, 0]
    .str.replace("m/", "", regex=False)  # remove prefix
    .str.replace("_", " ")  # convert underscores to spaces
    .str.lower()  # standardize lowercase
)

# =========================
# 4. CLEAN TITLES
# =========================
# Remove punctuation and lowercase titles for better matching

df_titles['clean_title'] = (
    df_titles.iloc[:, 0]
    .str.lower()
    .str.replace(r"[^\w\s]", "", regex=True)  # remove punctuation
)

# =========================
# 5. PREPARE MATCHING LIST
# =========================
choices = df_links['clean_link'].dropna().unique()


# =========================
# 6. FUZZY MATCH FUNCTION
# =========================
def match_title(title):
    """
    Takes a movie title and finds the closest matching slug.
    Returns:
    - best match string
    - similarity score (0–100)
    """
    match = process.extractOne(
        title,
        choices,
        scorer=fuzz.token_sort_ratio
    )

    if match:
        return pd.Series([match[0], match[1]])

    return pd.Series([None, 0])


# Apply matching to every title
df_titles[['matched_link', 'match_score']] = df_titles['clean_title'].apply(match_title)

# =========================
# 7. CHECK MATCH QUALITY
# =========================
print("Match score summary:")
print(df_titles['match_score'].describe())

# Optional: inspect weak matches
print("\nLow confidence matches:")
print(df_titles[df_titles['match_score'] < 85].head())

# =========================
# 8. FILTER GOOD MATCHES
# =========================
# Keep only reliable matches (you can adjust threshold: 80–90)

df_titles = df_titles[df_titles['match_score'] >= 85]

# =========================
# 9. MERGE DATASETS
# =========================
merged = df_titles.merge(
    df_links,
    left_on='matched_link',
    right_on='clean_link',
    how='left'
)

# =========================
# 10. CHECK OUTPUT
# =========================
print("\nMerged dataset preview:")
print(merged.head())

print("\nFinal shape:")
print(merged.shape)

# =========================
# 11. SAVE FINAL FILE
# =========================
output_path = r"Outputs&ExcelFiles\MovieTitlesMerging\merged_movies.xlsx"

merged.to_excel(output_path, index=False)

print("Saved successfully to GitHub repository folder:")
print(output_path)
from pathlib import Path
from collections import Counter
import re

import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS


# Step 1: Set file path
INPUT_PATH = Path("Outputs&ExcelFiles/KaggleData/rotten_tomatoes_critic_reviews (PreRelease).xlsx")

OUTPUT_DIR = Path("Outputs&ExcelFiles/TextAnalysisOutput")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Step 2: Define the two lexicons
# Gneric praise/pan adjectives ("brilliant," "terrible," "boring," "amazing") are left out on purpose
HYPE_WORDS = {
    # Cinematic universe / franchise branding
    "mcu", "dcu", "dceu", "marvel", "universe", "multiverse",
    "franchise", "canon", "lore", "crossover", "shared-universe",
    "connected-universe",
    # Sequel/prequel/series language
    "sequel", "sequels", "prequel", "prequels", "trilogy", "saga",
    "reboot", "rebooted", "remake", "remakes", "spinoff", "spin-off",
    "installment", "instalment", "chapter", "predecessor",
    "predecessors", "follow-up", "followup", "continuation", "entry",
    "finale", "conclusion",
    # Anticipation / buzz / marketing
    "anticipated", "anticipation", "hype", "hyped", "overhyped",
    "buzz", "buzzworthy", "blockbuster", "tentpole", "marketing",
    "trailer", "trailers", "teaser", "teasers", "merchandise",
    "merchandising", "tie-in", "tie-ins", "presold", "pre-sold",
    "opening-weekend", "boxoffice", "box-office",
    # Fan culture / nostalgia
    "fan", "fans", "fandom", "fanbase", "fanservice", "fan-service",
    "nostalgia", "nostalgic", "beloved", "iconic", "legacy",
    "die-hard", "diehard", "cameo", "cameos", "easter-egg",
    "easter-eggs", "stinger", "post-credits", "mid-credits",
    # Genre/brand shorthand that signals franchise machinery
    "superhero", "superheroes", "comic-book", "popcorn", "tentpoles",
    "summer-blockbuster", "studio-tentpole", "brand", "ip",
}

QUALITY_WORDS = {
    # Performance / casting
    "acting", "performance", "performances", "casting", "cast",
    "actor", "actress", "actors", "actresses", "portrayal",
    "portrays", "ensemble", "chemistry", "lead", "supporting",
    "miscast", "underacted", "overacted", "scenery-chewing",
    # Direction / authorship
    "direction", "directing", "director", "directorial", "auteur",
    "vision", "helmer", "filmmaker", "filmmaking", "craftsmanship",
    "craft", "polished", "technical", "technically",
    # Writing / story construction
    "screenplay", "script", "writing", "screenwriter",
    "screenwriters", "writer-director", "dialogue", "dialog",
    "plot", "plotting", "subplot", "subplots", "narrative",
    "storytelling", "story", "structure", "pacing", "pace", "arc",
    "character-development", "characterization", "underwritten",
    "overwritten", "well-written", "tightly-written",
    # Visual / technical craft
    "cinematography", "cinematographer", "camerawork", "framing",
    "composition", "lighting", "visuals", "visual", "cgi",
    "special-effects", "visual-effects", "production-design",
    "art-direction", "costume", "costumes", "costume-design",
    "set-design", "set-piece", "choreography", "editing", "editor",
    "score", "soundtrack", "sound-design",
    # Tone / nuance (descriptive craft vocabulary, not generic praise)
    "nuance", "nuanced", "subtlety", "subtle", "tone", "atmosphere",
    "texture", "restraint", "understated", "layered", "depth",
    "authentic", "authenticity", "tension", "world-building",
}

# Multi-word phrases
HYPE_PHRASES = {
    "fan service", "box office", "cinematic universe", "comic book",
    "comic-book movie", "origin story", "easter egg", "easter eggs",
    "long awaited", "long-awaited", "highly anticipated",
    "much anticipated", "much-anticipated", "fan favorite",
    "fan-favorite", "beloved character", "beloved characters",
    "die hard fan", "die-hard fan", "summer blockbuster",
    "popcorn movie", "popcorn flick", "shared universe",
    "expanded universe", "next chapter", "final chapter",
    "in the series", "of the series", "film series", "movie series",
    "this series", "the series", "in this franchise",
}
QUALITY_PHRASES = {
    "production design", "character development", "visual storytelling",
    "narrative structure", "special effects", "visual effects",
    "set design", "set piece", "set pieces", "sound design",
    "art direction", "costume design", "lead actor", "lead actress",
    "supporting cast", "well written", "tightly written",
    "beautifully shot", "gorgeously shot", "visually stunning",
    "world building",
}


# Step 3: Helper functions
def clean_whitespace(text: str) -> str:
    """Collapse repeated spaces/tabs/newlines into single spaces"""
    return re.sub(r"\s+", " ", str(text)).strip()


def tokenize_words(text: str) -> list[str]:
    """Lowercase word tokens, keep hyphenated words"""
    tokens = re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", text)
    return [t.lower() for t in tokens]


def count_phrase_hits(text_lower: str, phrases: set[str]) -> int:
    """Count occurrences of multi-word phrases in the raw lowercase text"""
    return sum(text_lower.count(phrase) for phrase in phrases)


def score_review(review_text: str) -> dict:
    """Tokenize review and return hype/quality counts and normalized scores"""
    text = clean_whitespace(review_text)
    text_lower = text.lower()
    words = tokenize_words(text)
    total_words = len(words)

    hype_hits = sum(1 for w in words if w in HYPE_WORDS)
    hype_hits += count_phrase_hits(text_lower, HYPE_PHRASES)

    quality_hits = sum(1 for w in words if w in QUALITY_WORDS)
    quality_hits += count_phrase_hits(text_lower, QUALITY_PHRASES)

    # Normalize by review length. Guard against empty reviews.
    hype_score = hype_hits / total_words if total_words > 0 else 0.0
    quality_score = quality_hits / total_words if total_words > 0 else 0.0

    diff = hype_score - quality_score

    NEUTRAL_BAND = 0.0

    if hype_hits == 0 and quality_hits == 0:
        label = "Neither"
    elif diff > NEUTRAL_BAND:
        label = "Hype"
    elif diff < -NEUTRAL_BAND:
        label = "Quality"
    else:
        label = "Mixed"

    return {
        "hype_word_count": hype_hits,
        "quality_word_count": quality_hits,
        "total_words": total_words,
        "hype_score": round(hype_score, 4),
        "quality_score": round(quality_score, 4),
        "score_diff": round(diff, 4),
        "label": label,
    }


# Step 4: Load the Excel file
df = pd.read_excel(INPUT_PATH)

# Drop rows with no review text
df = df[df["review_content"].notna()].copy()

# Step 5: Score every review
scored = df["review_content"].apply(score_review).apply(pd.Series)
df = pd.concat([df, scored], axis=1)


# Step 6: Save the full row-level results.
detailed_path = OUTPUT_DIR / "reviews_with_hype_quality_scores.xlsx"
df.to_excel(detailed_path, index=False)


# Step 7: Aggregate per movie
movie_summary = (
    df.groupby("Title")
    .agg(
        Superhero=("Superhero", "first"),
        review_count=("review_content", "count"),
        avg_hype_score=("hype_score", "mean"),
        avg_quality_score=("quality_score", "mean"),
        avg_score_diff=("score_diff", "mean"),
        pct_hype=("label", lambda s: (s == "Hype").mean()),
        pct_quality=("label", lambda s: (s == "Quality").mean()),
        pct_mixed=("label", lambda s: (s == "Mixed").mean()),
        pct_neither=("label", lambda s: (s == "Neither").mean()),
    )
    .round(4)
    .sort_values("avg_score_diff", ascending=False)
)

movie_summary_path = OUTPUT_DIR / "movie_hype_quality_summary.xlsx"
movie_summary.to_excel(movie_summary_path)
print(f"Saved per-movie summary to: {movie_summary_path}")


# Step 8: Aggregate by top_critic
critic_summary = (
    df.groupby("top_critic")
    .agg(
        review_count=("review_content", "count"),
        avg_hype_score=("hype_score", "mean"),
        avg_quality_score=("quality_score", "mean"),
        pct_hype=("label", lambda s: (s == "Hype").mean()),
        pct_quality=("label", lambda s: (s == "Quality").mean()),
    )
    .round(4)
)
print("\nHype vs. Quality language by top_critic status:")
print(critic_summary)


# Step 9: Overall label breakdown
label_counts = df["label"].value_counts()
label_pct = (label_counts / len(df) * 100).round(1)
print("\nOverall label breakdown:")
for lbl in label_counts.index:
    print(f"  {lbl}: {label_counts[lbl]:,} reviews ({label_pct[lbl]}%)")


# Step 10: Word clouds for Hype-labeled vs Quality-labeled reviews
custom_stopwords = set(STOPWORDS)

def build_wordcloud(text_series: pd.Series, out_path: Path, title: str) -> None:
    combined_text = " ".join(text_series.astype(str).tolist())
    tokens = [
        t for t in tokenize_words(combined_text)
        if len(t) > 2 and t not in custom_stopwords
    ]
    clean_text = " ".join(tokens)
    if not clean_text.strip():
        print(f"  Skipping {title} word cloud -- no words to plot.")
        return
    wc = WordCloud(
        width=1200, height=700, background_color="white",
        colormap="viridis", random_state=42,
    ).generate(clean_text)
    plt.figure(figsize=(12, 7))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title(title, fontsize=16)
    plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path}")


build_wordcloud(
    df.loc[df["label"] == "Hype", "review_content"],
    OUTPUT_DIR / "wordcloud_hype.png",
    "Hype-labeled reviews",
)
build_wordcloud(
    df.loc[df["label"] == "Quality", "review_content"],
    OUTPUT_DIR / "wordcloud_quality.png",
    "Quality-labeled reviews",
)
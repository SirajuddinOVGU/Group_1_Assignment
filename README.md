# The Effect of Critic Reviews on Opening Weekend Box Office Performance #

#### Master Seminar Research Term Paper — Media Economics Seminar ####
#### Otto von Guericke University Magdeburg, Faculty of Economics and Management, Summer Term 2026 ####

Authors: MSBAH, YKC, PKM

## Project Overview ##

We evaluate if the Rotten Tomatoes’ critic's review scores (Tomatomer Score) are positively correlated with opening weekend box office revenue (U.S.-wide-released films) during the years 2015-2019. The use of opening weekend revenue as a measure provides an early indication of consumers' interest in a film when information about that film's quality prior to its release (pre-release signal, particularly based on critics’ reviews) would have the greatest impact on their decision-making. We ensured that the data used for critics' score and review content is specific to before the movies were released, ensuring the data is not affected by post-release reviews and negates word-of-mouth effects. By the time opening weekend revenue has been established, word of mouth from a broad audience may be impacting subsequent ticket sales.

Our study address the following Research Question: 
#### What is the relationship between Rotten Tomatoes review metrics and opening weekend box office performance? #### 

Based on this research question we test two hypotheses:
#### H1: Higher Rotten Tomatoes critic ratings are positively associated with opening weekend domestic box-office revenue. ####
#### H2: Superhero movie reviews contain significantly more hype-related language than non-superhero reviews, relative to quality-related language. ####

H1 is tested using OLS regression, controlling for production budget, franchise status, review volume, and release year. H2 is tested using a lexicon-based text analysis of pre-release critic review content, comparing hype vs. quality language across superhero and non superhero film reviews.

## Data sources ##
- Box office Mojo - Movie name, opening weekend revenue, release date, production budget
- Rotten Tomatoes - Tomatometer scores, number of critic reviews 
- Kaggle - Tomatometer movie review dataset, Independent Tomamtometer scores
- Wikipedia - Production budget
- Claude (AI model) - Franchise status (0/1), Superhero and non-superhero (0/1)


## Methodology ##
#### Regression Analysis ####
- Model 1 - ln(Opening Weekend Grossi)=0+1Tomatometeri+it
- Model 2 - ln(Opening Weekend Grossi)=0+1Tomatometeri+2ln(Volumei)+it
- Model 3 - ln(Opening Weekend Grossi)=0+1Tomatometeri+2ln(Volumei)+3Franchisei+4ln(Budgeti)+5Yeari+it

#### Text Analysis ####
- Create two custom dictionaries : Hype related and Quality related
- Calculate hype score and quality score
- Classify the review into : Hype, Quality, Mixed or Neither

#### Variables ####
- Dependent variable - Opening Weekend gross (Opening Weekend Box office revenue)
- Independent variable - Tomatometer score
- Control variables - Review volume, Budget, Franchise, Time trend

## Repository Structure ##
1. Data - Raw data, Intermediate, Final Data
3. Scripts - Scraping, Data preparation, Regression, Text Analysis
4. Outputs&Excel Files - Regression output, Text Analysis output


## Limitations ##
- This analysis is observational so results does not reflect casual effects
- The model does not control for competing releases in the same week.
- Sample is limited to  US wide release between 2015 - 2019 which avoids the effects of COVID 19 in film industry.


-----------------------------------------------------------------------
TASK DIVISION/CONTRIBUTIONS
-----------------------------------------------------------------------
MSBAH 
1) Brainstormed for ideas, established topic of interest for research, directed flow and progress of work.
2) Prepared baseline and pre-released data, data-cleaning, data checking and verification, finalized data for regression and text analysis
3) Prepared python script for movie title merging (for text analysis), python script for Regression, and python script for review text analysis (including lexicons)
4) Interpreted and prepared summaries for regression and text analysis results
5) Prepared literature review and results section in group report and slides
-----------------------------------------------------------------------
YKC
1)

-----------------------------------------------------------------------
PKM
1)

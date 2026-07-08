# The Effect of Critic Reviews on Opening Weekend Box Office Performance #

#### Master Seminar Research Term Paper — Media Economics Seminar ####
#### Otto von Guericke University Magdeburg, Faculty of Economics and Management, Summer Term 2026 ####

Authors: Muhammad Sirajuddin Bin Abd Halim, Yashoda K C, Poon Kar Mun

## Project Overview ##

This project examines whether Rotten Tomatoes critic review metrics — the Tomatometer score and review volume — are associated with opening weekend box office revenue for wide-release films in the US market between 2015 and 2019. Opening weekend revenue is used because it captures consumer demand at the point where pre-release information signals (critic reviews in particular) are expected to matter most, before word-of-mouth from general audiences can shape later decisions.

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

# Evaluation report — dev40_extract4b: split=dev, visits=40, gold codes=60 (majority ≥2/3)

## Final codes
- Exact code: P=0.250 R=0.250 F1=0.250
- 3-char category (lenient): P=0.433 R=0.433 F1=0.433
- Visit exact-set match: 0.175
- Precision vs ANY annotator: 0.250
- Predicted codes per visit: 1.50 (gold 1.50)

## Per-visit (multi-label) metrics
Micro P/R/F1 above pools all (visit, code) pairs; here every visit counts once.
- Per-visit average: P=0.248 R=0.229 F1=0.234 Jaccard=0.215
- Exact set match 0.17; all gold codes found 0.17; at least one found 0.30

| Gold codes in visit | Visits | Micro P / R / F1 | Per-visit F1 | Exact set match | Gold found: all / some / none (visits) | Codes predicted per visit |
|---|---|---|---|---|---|---|
| 1 | 23 | 0.208 / 0.217 / 0.213 | 0.217 | 0.22 | 5 / 0 / 18 | 1.04 |
| 2 | 14 | 0.192 / 0.179 / 0.185 | 0.195 | 0.07 | 1 / 3 / 10 | 1.86 |
| 3 | 3 | 0.500 / 0.556 / 0.526 | 0.540 | 0.33 | 1 / 2 / 0 | 3.33 |

## Human ceiling (pairwise annotator agreement, same visits)
- DR_A vs DR_B: P=1.000 R=0.967 F1=0.983
- DR_A vs DR_C: P=0.914 R=0.964 F1=0.938
- DR_B vs DR_C: P=0.917 R=1.000 F1=0.957

## Stage recalls (billable gold codes)
- Chapter Recall@3 (any diagnosis of the visit): 53/60 = 0.883
- Section Recall@3 (any diagnosis of the visit): 34/60 = 0.567
- Diagnosis extracted (matched by eval judge): 43/60 = 0.717
- Chapter recall given extracted: 38/43 = 0.884
- Section recall given extracted: 27/43 = 0.628
- Gold reached the final candidate list: 23/60 = 0.383
- Final choice correct when gold reached the final list: 12/23 = 0.522

## Where each gold code ends up (first failing stage)
- correct: 15 (25.0%)
- diagnosis never extracted: 14 (23.3%)
- extracted, wrong CHAPTER: 5 (8.3%)
- extracted, right chapter, wrong SECTION: 11 (18.3%)
- extracted, lost in CATEGORY/deeper narrowing: 4 (6.7%)
- reached final list, wrong FINAL choice: 11 (18.3%)

## False positives
- different category (extra/wrong diagnosis): 34
- same 3-char category as a gold code (granularity): 11

## Validity & cost
- Valid billable codes: 60/60
- Evidence verbatim in note: 54/63 diagnoses (others snapped to the closest note line)
- Diagnoses extracted per visit: 1.57; NONE answers: 1
- Narrowing depth per diagnosis: {0: 26, 1: 30, 2: 7}
- Final candidate list size: mean 39.5, max 99
- Seconds/visit: 18.5; LLM calls/visit: 6.8

## Step-by-step details

### Path per extracted diagnosis (MAX_CODES = 100)
- Section → code directly (≤ 100 codes under the chosen sections): 26/63 (41%)
- Section → category (→ deeper) → code (> 100 codes): 37/63 (59%); narrowing levels used: {1: 30, 2: 7}
- Codes under the chosen sections — direct path: mean 55.2, median 60, max 99; narrowed path: mean 404.5, median 297, max 1269

### Options shown to the model at each step (per diagnosis)
- Chapter step: 22 options; chapters chosen: mean 1.5, median 1, max 3
- Section step: options mean 19.0, median 17, max 47; sections chosen: mean 1.6, median 1, max 3
- Category step (37 diagnoses): options mean 18.1, median 17, max 47; codes left after it mean 53.2, median 31, max 211
- Deeper level 2 (7 diagnoses): options mean 11.4, median 11, max 27; codes left after it mean 17.3, median 6, max 62
- Final code step: candidates mean 39.5, median 30, max 99 (direct path mean 55.2, median 60, max 99; narrowed path mean 28.4, median 24, max 87)

### Step accuracy (gold codes whose diagnosis was extracted; each step given the previous one was right)
- Chapter: gold chapter among chosen chapters: 38/43 = 0.884
- Section: gold section among chosen sections | chapter right: 27/38 = 0.711
- Category: gold category kept at the category step | section right & narrowing ran: 12/14 = 0.857
- Narrowing overall: gold still in final candidates | section right & narrowing ran: 10/14 = 0.714
- Code: correct final code | gold in candidates: 12/23 = 0.522 (direct path 7/13 = 0.538; narrowed path 5/10 = 0.500)
- End to end, for extracted diagnoses: 12/43 = 0.279

### Confidence (final step only; no threshold is applied by the system)
- high (0.9): 55 codes, precision 0.273
- medium (0.6): 5 codes, precision 0.000
- If only codes with score ≥ 0.3 were returned: P=0.250 R=0.250 F1=0.250
- If only codes with score ≥ 0.6 were returned: P=0.250 R=0.250 F1=0.250
- If only codes with score ≥ 0.9 were returned: P=0.273 R=0.250 F1=0.261

## Failure examples

### V0008  gold=['E87.6', 'L25.9']  pred=['L23.9', 'E61.2']
```
ביקור מרפאתי. בן 35.
תועד גם: אריתמה וקילוף באזור החשיפה.
מהשיחה ומהתיק: פריחה אחרי חשיפה לחומר חדש, טרם סווג המנגנון.
הערכה קלינית ראשונית: דרמטיטיס ממגע לא מסווגת.
בנוסף, נדונה בעיה נפרדת: חולשה והתכווצויות לאחר הקאות מרובות.
הממצא המחזק את התלונה הנוספת: אשלגן 2.9.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **Contact dermatitis, unspecified** | chapters ['ch12'] → sections ['L20-L30'] (74 codes) → 74 cands → **L23.9** (high)
- **Muscle weakness and cramps due to frequent bowel movements, with low magnesium level (magnesium 2.9)** | chapters ['ch13', 'ch4', 'ch18'] → sections ['M60-M63', 'E50-E64', 'R25-R29'] (542 codes) → E61(10) → 10 cands → **E61.2** (high)
  - gold E87.6 [matched dx: Muscle weakness and cramps due to frequent bowel movements, with low magnesium level (magnesium 2.9)]: Ch.4 Endocrine, nutritional and metabolic diseases (E00-E89) > Metabolic disorders (E70-E88) > E87 Other disorders of fluid, electrolyte and acid-base balance > E87.6 Hypokalemia
  - gold L25.9 [matched dx: Contact dermatitis, unspecified]: Ch.12 Diseases of the skin and subcutaneous tissue (L00-L99) > Dermatitis and eczema (L20-L30) > L25 Unspecified contact dermatitis > L25.9 Unspecified contact dermatitis, unspecified cause

### V0009  gold=['H61.21']  pred=['H71.01']
```
ביקור מרפאתי. בן 68.
בהפניה מתוארת תמונה של ירידה פתאומית בשמיעה באוזן ימין ללא כאב.
בדיקות וממצאים: פקק צרומן מסתיר עור התוף.
הערכה קלינית ראשונית: פקק שעווה באוזן ימין.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **Hearing loss, right ear, acute** | chapters ['ch8'] → sections ['H65-H75'] (288 codes) → H71(20) → 20 cands → **H71.01** (high)
  - gold H61.21 [matched dx: Hearing loss, right ear, acute]: Ch.8 Diseases of the ear and mastoid process (H60-H95) > Diseases of external ear (H60-H62) > H61 Other disorders of external ear > H61.2 Impacted cerumen > H61.21 Impacted cerumen, right ear

### V0010  gold=['M05.79', 'M79.7']  pred=['M05.A', 'R44.9']
```
ביקור מרפאתי. בן 70.
בהפניה מתוארת תמונה של נפיחות סימטרית במפרקי אצבעות עם נוקשות בוקר ארוכה.
תועד גם: RF ו-anti-CCP חיוביים.
בנוסף, נדונה בעיה נפרדת: כאב מפושט, שינה לא מרעננת וקשיי ריכוז.
הממצא המחזק את התלונה הנוספת: רגישות נרחבת ללא דלקת מפרקים בבדיקה.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **Symmetric hand swelling with morning stiffness** | chapters ['ch13', 'ch18'] → sections ['M05-M14', 'M30-M36'] (1269 codes) → M05(211) → M05.A(1) → 1 cands → **M05.A** (high)
- **Rheumatoid arthritis** | chapters ['ch13'] → sections ['M05-M14'] (1185 codes) → M05(211) → M05.A(1) → 1 cands → **M05.A** (high)
- **Fibromyalgia** | chapters ['ch18', 'ch5', 'ch6'] → sections ['R25-R29', 'R40-R46', 'R50-R69'] (297 codes) → R52/R53/R44(13) → 13 cands → **R44.9** (high)
  - gold M05.79 [matched dx: Rheumatoid arthritis]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Inflammatory polyarthropathies (M05-M14) > M05 Rheumatoid arthritis with rheumatoid factor > M05.7 Rheumatoid arthritis with rheumatoid factor without organ or systems involvement > M05.79 Rheumatoid arthritis with rheumatoid factor of multiple sites without organ or systems involvement
  - gold M79.7 [matched dx: Fibromyalgia]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Other soft tissue disorders (M70-M79) > M79 Other and unspecified soft tissue disorders, not elsewhere classified > M79.7 Fibromyalgia

### V0013  gold=['G56.02', 'H25.11']  pred=['H25.011', 'G56.82']
```
ביקור מרפאתי. בן 60.
בבדיקה: עכירות גרעינית של העדשה.
בהפניה מתוארת תמונה של טשטוש ראייה מתקדם וסנוור בלילה בעין ימין.
הערכה קלינית ראשונית: קטרקט גרעיני תלוי גיל בעין ימין.
בנוסף, נדונה בעיה נפרדת: כאב ותחושת זרמים בכף יד שמאל בעת נהיגה.
הממצא המחזק את התלונה הנוספת: EMG מתאים ללחץ על העצב המדיאני משמאל.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **Cataract, right eye** | chapters ['ch7'] → sections ['H25-H28'] (119 codes) → H25(30) → 30 cands → **H25.011** (high)
- **Cervical radiculopathy, left side, due to median nerve compression** | chapters ['ch6', 'ch13'] → sections ['G50-G59'] (106 codes) → G56(28) → 28 cands → **G56.82** (high)
  - gold G56.02 [matched dx: Cataract, right eye]: Ch.6 Diseases of the nervous system (G00-G99) > Nerve, nerve root and plexus disorders (G50-G59) > G56 Mononeuropathies of upper limb > G56.0 Carpal tunnel syndrome > G56.02 Carpal tunnel syndrome, left upper limb
  - gold H25.11 [matched dx: Cataract, right eye]: Ch.7 Diseases of the eye and adnexa (H00-H59) > Disorders of lens (H25-H28) > H25 Age-related cataract > H25.1 Age-related nuclear cataract > H25.11 Age-related nuclear cataract, right eye

### V0020  gold=['F42.9']  pred=['F22']
```
ביקור מרפאתי. בן 55.
מהשיחה ומהתיק: מחשבות טורדניות על זיהום וטקסי רחצה חוזרים.
תועד גם: זמן רב מוקדש לבדיקות וניקיון.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **Paranoid delusions** | chapters ['ch5'] → sections ['F20-F29'] (18 codes) → 18 cands → **F22** (high)
  - gold F42.9 [matched dx: NONE]: Ch.5 Mental, Behavioral and Neurodevelopmental disorders (F01-F99) > Anxiety, dissociative, stress-related, somatoform and other nonpsychotic mental disorders (F40-F48) > F42 Obsessive-compulsive disorder > F42.9 Obsessive-compulsive disorder, unspecified

### V0024  gold=['N95.1']  pred=['E28.310']
```
ביקור מרפאתי. בת 70.
בהפניה מתוארת תמונה של גלי חום והזעות לילה סביב הפסקת המחזור.
ממצא תומך: שינוי בדפוסי הווסת בגיל המעבר.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **Menopausal transition** | chapters ['ch4'] → sections ['E20-E35'] (99 codes) → 99 cands → **E28.310** (high)
  - gold N95.1 [matched dx: Menopausal transition]: Ch.14 Diseases of the genitourinary system (N00-N99) > Noninflammatory disorders of female genital tract (N80-N98) > N95 Menopausal and other perimenopausal disorders > N95.1 Menopausal and female climacteric states

### V0044  gold=['D75.1']  pred=['D63.8']
```
ביקור מרפאתי. בן 55.
בימים האחרונים דווח כי רמות המוגלובין והמטוקריט גבוהות בעישון ממושך.
ממצא תומך: אריתרופואטין מוגבר.
סוכם על תוכנית טיפול ומעקב בהתאם לבעיות שנדונו בביקור.
```
- **Chronic kidney disease due to long-term smoking with elevated hemoglobin and hematocrit, supported by increased erythropoietin** | chapters ['ch14', 'ch3'] → sections ['N17-N19', 'D60-D64'] (44 codes) → 44 cands → **D63.8** (high)
  - gold D75.1 [matched dx: Chronic kidney disease due to long-term smoking with elevated hemoglobin and hematocrit, supported by increased erythropoietin]: Ch.3 Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism (D50-D89) > Other disorders of blood and blood-forming organs (D70-D77) > D75 Other and unspecified diseases of blood and blood-forming organs > D75.1 Secondary polycythemia

### V0045  gold=['N43.3']  pred=['R60.0']
```
ביקור מרפאתי. בן 56.
בהפניה מתוארת תמונה של נפיחות שק אשכים לא כואבת.
על פי המסמכים: באולטרסאונד נוזל סביב האשך.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **ascites of the scrotum** | chapters ['ch14', 'ch18'] → sections ['R10-R19', 'R30-R39', 'R50-R69'] (209 codes) → R37/R60(4) → 4 cands → **R60.0** (high)
  - gold N43.3 [matched dx: NONE]: Ch.14 Diseases of the genitourinary system (N00-N99) > Diseases of male genital organs (N40-N53) > N43 Hydrocele and spermatocele > N43.3 Hydrocele, unspecified

### V0048  gold=['A54.9', 'H91.92']  pred=['A54.00']
```
ביקור מרפאתי. בת 31.
בימים האחרונים דווח כי הפרשה וצריבה לאחר מגע מיני בלתי מוגן.
תועד גם: NAAT לגונוריאה חיובי.
תלונה נוספת שנבדקה: תלונה חדשה על שמיעה חלשה בצד שמאל.
לגבי הבעיה הנוספת נמצאו: נדרש בירור אודיולוגי נוסף.
סוכם על תוכנית טיפול ומעקב בהתאם לבעיות שנדונו בביקור.
```
- **Gonorrhea** | chapters ['ch1'] → sections ['A50-A64'] (142 codes) → A54(31) → 31 cands → **A54.00** (high)
- **Hearing loss of left ear** | chapters ['ch8'] → sections ['H80-H83'] (77 codes) → 77 cands → **NONE** (high)
  - gold A54.9 [matched dx: Gonorrhea]: Ch.1 Certain infectious and parasitic diseases (A00-B99) > Infections with a predominantly sexual mode of transmission (A50-A64) > A54 Gonococcal infection > A54.9 Gonococcal infection, unspecified
  - gold H91.92 [matched dx: Hearing loss of left ear]: Ch.8 Diseases of the ear and mastoid process (H60-H95) > Other disorders of ear (H90-H94) > H91 Other and unspecified hearing loss > H91.9 Unspecified hearing loss > H91.92 Unspecified hearing loss, left ear

### V0052  gold=['D53.9', 'I22.9']  pred=['I21.9', 'E46', 'D53.9']
```
הערכה דחופה במוקד. בת 40.
מתאר/ת כי לאחר אוטם טרי הופיע אירוע כלילי חד נוסף.
ממצא תומך: עלייה מחודשת בטרופונין עם שינויים איסכמיים.
נושא נוסף שהועלה בביקור: חולשה בחולה עם תזונה מוגבלת ומדדי דם חריגים.
לגבי הבעיה הנוספת נמצאו: טרם זוהה רכיב התזונה החסר.
נרשם גם: אנמיה תזונתית לא מסווגת.
נדרשת הערכה וטיפול דחופים במסגרת מתאימה; תואמה הפניה מיידית.
```
- **Acute myocardial infarction** | chapters ['ch9'] → sections ['I20-I25'] (94 codes) → 94 cands → **I21.9** (high)
- **Malnutrition** | chapters ['ch4', 'ch3'] → sections ['E40-E46', 'D50-D53'] (27 codes) → 27 cands → **E46** (high)
- **Undifferentiated nutritional anemia** | chapters ['ch3', 'ch4'] → sections ['D50-D53', 'E40-E46'] (27 codes) → 27 cands → **D53.9** (high)
  - gold D53.9 [matched dx: Undifferentiated nutritional anemia]: Ch.3 Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism (D50-D89) > Nutritional anemias (D50-D53) > D53 Other nutritional anemias > D53.9 Nutritional anemia, unspecified
  - gold I22.9 [matched dx: Acute myocardial infarction]: Ch.9 Diseases of the circulatory system (I00-I99) > Ischemic heart diseases (I20-I25) > I22 Subsequent ST elevation (STEMI) and non-ST elevation (NSTEMI) myocardial infarction > I22.9 Subsequent ST elevation (STEMI) myocardial infarction of unspecified site

### V0057  gold=['H11.002']  pred=['H00.016']
```
ביקור מרפאתי. בן 27.
מתאר/ת כי תחושת גוף זר והפרעה קוסמטית בעין שמאל.
על פי המסמכים: פטריגיום נזלי נראה בבדיקה.
הערכה קלינית ראשונית: פטריגיום בעין שמאל.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **D09.01** | chapters ['ch7'] → sections ['H00-H05'] (574 codes) → H00(28) → 28 cands → **H00.016** (high)
  - gold H11.002 [matched dx: NONE]: Ch.7 Diseases of the eye and adnexa (H00-H59) > Disorders of conjunctiva (H10-H11) > H11 Other disorders of conjunctiva > H11.0 Pterygium of eye > H11.00 Unspecified pterygium of eye > H11.002 Unspecified pterygium of left eye

### V0060  gold=['K56.609']  pred=['K59.1']
```
ביקור מרפאתי. בן 30.
מגיע/ה לבדיקה עקב הקאות חוזרות, נפיחות ואי מעבר גזים.
על פי המסמכים: צילום בטן עם לולאות מורחבות.
סוכם על תוכנית טיפול ומעקב בהתאם לבעיות שנדונו בביקור.
```
- **Chronic diarrhea** | chapters ['ch11', 'ch18'] → sections ['K50-K52', 'K55-K64', 'R10-R19'] (347 codes) → K59/R14/R19(44) → 44 cands → **K59.1** (high)
  - gold K56.609 [matched dx: NONE]: Ch.11 Diseases of the digestive system (K00-K95) > Other diseases of intestines (K55-K64) > K56 Paralytic ileus and intestinal obstruction without hernia > K56.6 Other and unspecified intestinal obstruction > K56.60 Unspecified intestinal obstruction > K56.609 Unspecified intestinal obstruction, unspecified as to partial versus complete obstruction

### V0069  gold=['F45.1']  pred=['F45.0']
```
ביקור מרפאתי. בת 63.
תועד גם: מצוקה ותפקוד ירוד סביב התסמינים.
מהשיחה ומהתיק: עיסוק מוגבר בתלונות גופניות למרות בירור נרחב.
הערכה קלינית ראשונית: הפרעת תסמינים סומטיים.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **Somatic symptom disorder** | chapters ['ch5'] → sections ['F40-F48'] (71 codes) → 71 cands → **F45.0** (high)
  - gold F45.1 [matched dx: Somatic symptom disorder]: Ch.5 Mental, Behavioral and Neurodevelopmental disorders (F01-F99) > Anxiety, dissociative, stress-related, somatoform and other nonpsychotic mental disorders (F40-F48) > F45 Somatoform disorders > F45.1 Undifferentiated somatoform disorder

### V0072  gold=['M34.9']  pred=['M34.0']
```
ביקור מרפאתי. בת 39.
ממצא תומך: ממצאים אופייניים בסקלרודקטיליה.
מהשיחה ומהתיק: התקשות עור אצבעות עם ריינו וצרבת.
לא הועלתה תלונה חריפה נוספת מעבר לנושאים שנדונו.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **Scleroderma** | chapters ['ch13'] → sections ['M30-M36'] (84 codes) → 84 cands → **M34.0** (high)
  - gold M34.9 [matched dx: Scleroderma]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Systemic connective tissue disorders (M30-M36) > M34 Systemic sclerosis [scleroderma] > M34.9 Systemic sclerosis, unspecified

### V0080  gold=['H40.1122', 'M33.20']  pred=['H47.012', 'R74.9']
```
ביקור מרפאתי. בן 31.
בימים האחרונים דווח כי ירידה מתמשכת בסיבי עצב הראייה משמאל.
תועד גם: OCT ושדה ראייה מתאימים לשלב בינוני.
בנוסף, נדונה בעיה נפרדת: חולשה שרירית פרוקסימלית וקושי לקום מכיסא.
לגבי הבעיה הנוספת נמצאו: CK גבוה מאוד.
סוכם על תוכנית טיפול ומעקב בהתאם לבעיות שנדונו בביקור.
```
- **Chronic progressive visual nerve dysfunction, left eye** | chapters ['ch7', 'ch6'] → sections ['H46-H47'] (92 codes) → 92 cands → **H47.012** (high)
- **Proximal muscle weakness and difficulty standing from sitting, with elevated CK** | chapters ['ch13', 'ch18'] → sections ['M60-M63', 'R25-R29', 'R70-R79'] (537 codes) → M60/R26/R74(121) → M60.8/R26.2/R74.9(26) → 26 cands → **R74.9** (high)
  - gold H40.1122 [matched dx: NONE]: Ch.7 Diseases of the eye and adnexa (H00-H59) > Glaucoma (H40-H42) > H40 Glaucoma > H40.1 Open-angle glaucoma > H40.11 Primary open-angle glaucoma > H40.112 Primary open-angle glaucoma, left eye > H40.1122 Primary open-angle glaucoma, left eye, moderate stage
  - gold M33.20 [matched dx: Proximal muscle weakness and difficulty standing from sitting, with elevated CK]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Systemic connective tissue disorders (M30-M36) > M33 Dermatopolymyositis > M33.2 Polymyositis > M33.20 Polymyositis, organ involvement unspecified
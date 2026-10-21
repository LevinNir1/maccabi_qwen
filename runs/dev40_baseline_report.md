# Evaluation report — dev40_baseline: split=dev, visits=40, gold codes=60 (majority ≥2/3)

## Final codes
- Exact code: P=0.182 R=0.167 F1=0.174
- 3-char category (lenient): P=0.296 R=0.267 F1=0.281
- Visit exact-set match: 0.100
- Precision vs ANY annotator: 0.182
- Predicted codes per visit: 1.38 (gold 1.50)

## Per-visit (multi-label) metrics
Micro P/R/F1 above pools all (visit, code) pairs; here every visit counts once.
- Per-visit average: P=0.179 R=0.163 F1=0.167 Jaccard=0.146
- Exact set match 0.10; all gold codes found 0.10; at least one found 0.23

| Gold codes in visit | Visits | Micro P / R / F1 | Per-visit F1 | Exact set match | Gold found: all / some / none (visits) | Codes predicted per visit |
|---|---|---|---|---|---|---|
| 1 | 23 | 0.190 / 0.174 / 0.182 | 0.174 | 0.17 | 4 / 0 / 19 | 0.91 |
| 2 | 14 | 0.111 / 0.107 / 0.109 | 0.107 | 0.00 | 0 / 3 / 11 | 1.93 |
| 3 | 3 | 0.429 / 0.333 / 0.375 | 0.389 | 0.00 | 0 / 2 / 1 | 2.33 |

## Human ceiling (pairwise annotator agreement, same visits)
- DR_A vs DR_B: P=1.000 R=0.967 F1=0.983
- DR_A vs DR_C: P=0.914 R=0.964 F1=0.938
- DR_B vs DR_C: P=0.917 R=1.000 F1=0.957

## Stage recalls (billable gold codes)
- Chapter Recall@3 (any diagnosis of the visit): 48/60 = 0.800
- Section Recall@3 (any diagnosis of the visit): 19/60 = 0.317
- Diagnosis extracted (matched by eval judge): 45/60 = 0.750
- Chapter recall given extracted: 30/45 = 0.667
- Section recall given extracted: 16/45 = 0.356
- Gold reached the final candidate list: 14/60 = 0.233
- Final choice correct when gold reached the final list: 8/14 = 0.571

## Where each gold code ends up (first failing stage)
- correct: 10 (16.7%)
- diagnosis never extracted: 14 (23.3%)
- extracted, wrong CHAPTER: 14 (23.3%)
- extracted, right chapter, wrong SECTION: 14 (23.3%)
- extracted, lost in CATEGORY/deeper narrowing: 2 (3.3%)
- reached final list, wrong FINAL choice: 6 (10.0%)

## False positives
- different category (extra/wrong diagnosis): 38
- same 3-char category as a gold code (granularity): 7

## Validity & cost
- Valid billable codes: 55/55
- Evidence verbatim in note: 60/70 diagnoses (others snapped to the closest note line)
- Diagnoses extracted per visit: 1.75; NONE answers: 15
- Narrowing depth per diagnosis: {0: 34, 1: 29, 2: 6, 3: 1}
- Final candidate list size: mean 38.0, max 99
- Seconds/visit: 14.2; LLM calls/visit: 5.6

## Step-by-step details

### Path per extracted diagnosis (MAX_CODES = 100)
- Section → code directly (≤ 100 codes under the chosen sections): 34/70 (49%)
- Section → category (→ deeper) → code (> 100 codes): 36/70 (51%); narrowing levels used: {1: 29, 2: 6, 3: 1}
- Codes under the chosen sections — direct path: mean 46.6, median 29, max 99; narrowed path: mean 381.8, median 274, max 1427

### Options shown to the model at each step (per diagnosis)
- Chapter step: 22 options; chapters chosen: mean 1.4, median 1, max 3
- Section step: options mean 18.2, median 12, max 43; sections chosen: mean 1.4, median 1, max 3
- Category step (36 diagnoses): options mean 14.1, median 12, max 35; codes left after it mean 66.9, median 23, max 352
- Deeper level 2 (7 diagnoses): options mean 14.4, median 11, max 31; codes left after it mean 45.9, median 24, max 120
- Deeper level 3 (1 diagnoses): options mean 24.0, median 24, max 24; codes left after it mean 5.0, median 5, max 5
- Final code step: candidates mean 38.0, median 23, max 99 (direct path mean 46.6, median 29, max 99; narrowed path mean 29.8, median 18, max 97)

### Step accuracy (gold codes whose diagnosis was extracted; each step given the previous one was right)
- Chapter: gold chapter among chosen chapters: 30/45 = 0.667
- Section: gold section among chosen sections | chapter right: 16/30 = 0.533
- Category: gold category kept at the category step | section right & narrowing ran: 7/8 = 0.875
- Narrowing overall: gold still in final candidates | section right & narrowing ran: 6/8 = 0.750
- Code: correct final code | gold in candidates: 8/14 = 0.571 (direct path 4/8 = 0.500; narrowed path 4/6 = 0.667)
- End to end, for extracted diagnoses: 8/45 = 0.178

### Confidence (final step only; no threshold is applied by the system)
- high (0.9): 32 codes, precision 0.281
- medium (0.6): 12 codes, precision 0.083
- low (0.3): 11 codes, precision 0.000
- If only codes with score ≥ 0.3 were returned: P=0.182 R=0.167 F1=0.174
- If only codes with score ≥ 0.6 were returned: P=0.227 R=0.167 F1=0.192
- If only codes with score ≥ 0.9 were returned: P=0.281 R=0.150 F1=0.196

## Failure examples

### V0004  gold=['Z23']  pred=['Z00.00']
```
ביקור מרפאתי. בן 74.
על פי המסמכים: אין מחלת חום פעילה בבדיקה.
מגיע/ה לבדיקה עקב הגעה לקבלת חיסון עונתי.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **Routine preventive visit for seasonal vaccination** | chapters ['ch21'] → sections ['Z00-Z13'] (156 codes) → Z00(13) → 13 cands → **Z00.00** (high)
  - gold Z23 [matched dx: Routine preventive visit for seasonal vaccination]: Ch.21 Factors influencing health status and contact with health services (Z00-Z99) > Persons with potential health hazards related to communicable diseases (Z20-Z29) > Z23 Encounter for immunization

### V0006  gold=['E55.9', 'H10.13', 'H52.4']  pred=['H10.13']
```
ביקור מרפאתי. בת 29.
בדיקות וממצאים: פפילות בלחמית ללא הפרשה מוגלתית.
מגיע/ה לבדיקה עקב גרד ודמעת בשתי העיניים אחרי חשיפה לאבקנים.
בנוסף, נדונה בעיה נפרדת: קושי לקרוא טקסט קטן לאחר גיל ארבעים.
הנתונים הרלוונטיים לכך: נדרש תיקון לקרוב למרות ראייה טובה למרחק.
נושא נוסף שהועלה בביקור: כאבי שרירים לא ספציפיים ובדיקת ויטמין D נמוכה.
הממצא המחזק את התלונה הנוספת: 25-OH Vitamin D מתחת לטווח.
לא הועלתה תלונה חריפה נוספת מעבר לנושאים שנדונו.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **allergic conjunctivitis** | chapters ['ch7'] → sections ['H10-H11'] (167 codes) → H10(72) → 72 cands → **H10.13** (high)
- **presbyopia** | chapters ['ch6'] → sections ['G35-G37'] (21 codes) → 21 cands → **NONE** (high)
- **vitamin D deficiency** | chapters ['ch3'] → sections ['D50-D53'] (19 codes) → 19 cands → **NONE** (high)
  - gold E55.9 [matched dx: vitamin D deficiency]: Ch.4 Endocrine, nutritional and metabolic diseases (E00-E89) > Other nutritional deficiencies (E50-E64) > E55 Vitamin D deficiency > E55.9 Vitamin D deficiency, unspecified
  - gold H10.13 [matched dx: allergic conjunctivitis]: Ch.7 Diseases of the eye and adnexa (H00-H59) > Disorders of conjunctiva (H10-H11) > H10 Conjunctivitis > H10.1 Acute atopic conjunctivitis > H10.13 Acute atopic conjunctivitis, bilateral
  - gold H52.4 [matched dx: presbyopia]: Ch.7 Diseases of the eye and adnexa (H00-H59) > Disorders of ocular muscles, binocular movement, accommodation and refraction (H49-H52) > H52 Disorders of refraction and accommodation > H52.4 Presbyopia

### V0008  gold=['E87.6', 'L25.9']  pred=['L23.9', 'G90.9']
```
ביקור מרפאתי. בן 35.
תועד גם: אריתמה וקילוף באזור החשיפה.
מהשיחה ומהתיק: פריחה אחרי חשיפה לחומר חדש, טרם סווג המנגנון.
הערכה קלינית ראשונית: דרמטיטיס ממגע לא מסווגת.
בנוסף, נדונה בעיה נפרדת: חולשה והתכווצויות לאחר הקאות מרובות.
הממצא המחזק את התלונה הנוספת: אשלגן 2.9.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **contact dermatitis, unspecified** | chapters ['ch12'] → sections ['L20-L30'] (74 codes) → 74 cands → **L23.9** (high)
- **muscle weakness and cramps after multiple bowel movements** | chapters ['ch12', 'ch6'] → sections ['L20-L30', 'G89-G99'] (186 codes) → G90(21) → 21 cands → **G90.9** (medium)
- **hypokalemia** | chapters ['ch3'] → sections ['D50-D53'] (19 codes) → 19 cands → **NONE** (high)
  - gold E87.6 [matched dx: hypokalemia]: Ch.4 Endocrine, nutritional and metabolic diseases (E00-E89) > Metabolic disorders (E70-E88) > E87 Other disorders of fluid, electrolyte and acid-base balance > E87.6 Hypokalemia
  - gold L25.9 [matched dx: contact dermatitis, unspecified]: Ch.12 Diseases of the skin and subcutaneous tissue (L00-L99) > Dermatitis and eczema (L20-L30) > L25 Unspecified contact dermatitis > L25.9 Unspecified contact dermatitis, unspecified cause

### V0009  gold=['H61.21']  pred=['H71.01']
```
ביקור מרפאתי. בן 68.
בהפניה מתוארת תמונה של ירידה פתאומית בשמיעה באוזן ימין ללא כאב.
בדיקות וממצאים: פקק צרומן מסתיר עור התוף.
הערכה קלינית ראשונית: פקק שעווה באוזן ימין.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **acute otitis externa of right ear** | chapters ['ch8'] → sections ['H65-H75'] (288 codes) → H71(20) → 20 cands → **H71.01** (high)
  - gold H61.21 [matched dx: NONE]: Ch.8 Diseases of the ear and mastoid process (H60-H95) > Diseases of external ear (H60-H62) > H61 Other disorders of external ear > H61.2 Impacted cerumen > H61.21 Impacted cerumen, right ear

### V0010  gold=['M05.79', 'M79.7']  pred=['M05.749', 'R29.898', 'M05.00']
```
ביקור מרפאתי. בן 70.
בהפניה מתוארת תמונה של נפיחות סימטרית במפרקי אצבעות עם נוקשות בוקר ארוכה.
תועד גם: RF ו-anti-CCP חיוביים.
בנוסף, נדונה בעיה נפרדת: כאב מפושט, שינה לא מרעננת וקשיי ריכוז.
הממצא המחזק את התלונה הנוספת: רגישות נרחבת ללא דלקת מפרקים בבדיקה.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **symmetric hand swelling with morning stiffness** | chapters ['ch13', 'ch13'] → sections ['M00-M02', 'M05-M14'] (1427 codes) → M05(211) → M05.7(24) → 24 cands → **M05.749** (high)
- **rheumatoid arthritis** | chapters ['ch13', 'ch13'] → sections ['M00-M02', 'M05-M14'] (1427 codes) → M05(211) → M05.0(23) → 23 cands → **M05.00** (low)
- **widespread hypersensitivity without joint inflammation** | chapters ['ch18'] → sections ['R25-R29'] (72 codes) → 72 cands → **R29.898** (high)
  - gold M05.79 [matched dx: rheumatoid arthritis]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Inflammatory polyarthropathies (M05-M14) > M05 Rheumatoid arthritis with rheumatoid factor > M05.7 Rheumatoid arthritis with rheumatoid factor without organ or systems involvement > M05.79 Rheumatoid arthritis with rheumatoid factor of multiple sites without organ or systems involvement
  - gold M79.7 [matched dx: NONE]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Other soft tissue disorders (M70-M79) > M79 Other and unspecified soft tissue disorders, not elsewhere classified > M79.7 Fibromyalgia

### V0013  gold=['G56.02', 'H25.11']  pred=['G56.02', 'H30.91']
```
ביקור מרפאתי. בן 60.
בבדיקה: עכירות גרעינית של העדשה.
בהפניה מתוארת תמונה של טשטוש ראייה מתקדם וסנוור בלילה בעין ימין.
הערכה קלינית ראשונית: קטרקט גרעיני תלוי גיל בעין ימין.
בנוסף, נדונה בעיה נפרדת: כאב ותחושת זרמים בכף יד שמאל בעת נהיגה.
הממצא המחזק את התלונה הנוספת: EMG מתאים ללחץ על העצב המדיאני משמאל.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **cataract, age-related, right eye** | chapters ['ch7'] → sections ['H30-H36'] (410 codes) → H30(56) → 56 cands → **H30.91** (medium)
- **median nerve compression, left upper extremity** | chapters ['ch6'] → sections ['G50-G59'] (106 codes) → G56(28) → 28 cands → **G56.02** (high)
  - gold G56.02 [matched dx: cataract, age-related, right eye]: Ch.6 Diseases of the nervous system (G00-G99) > Nerve, nerve root and plexus disorders (G50-G59) > G56 Mononeuropathies of upper limb > G56.0 Carpal tunnel syndrome > G56.02 Carpal tunnel syndrome, left upper limb
  - gold H25.11 [matched dx: cataract, age-related, right eye]: Ch.7 Diseases of the eye and adnexa (H00-H59) > Disorders of lens (H25-H28) > H25 Age-related cataract > H25.1 Age-related nuclear cataract > H25.11 Age-related nuclear cataract, right eye

### V0020  gold=['F42.9']  pred=['F03.94']
```
ביקור מרפאתי. בן 55.
מהשיחה ומהתיק: מחשבות טורדניות על זיהום וטקסי רחצה חוזרים.
תועד גם: זמן רב מוקדש לבדיקות וניקיון.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **obsessive-compulsive disorder** | chapters ['ch5'] → sections ['F01-F09'] (91 codes) → 91 cands → **F03.94** (medium)
  - gold F42.9 [matched dx: obsessive-compulsive disorder]: Ch.5 Mental, Behavioral and Neurodevelopmental disorders (F01-F99) > Anxiety, dissociative, stress-related, somatoform and other nonpsychotic mental disorders (F40-F48) > F42 Obsessive-compulsive disorder > F42.9 Obsessive-compulsive disorder, unspecified

### V0024  gold=['N95.1']  pred=[]
```
ביקור מרפאתי. בת 70.
בהפניה מתוארת תמונה של גלי חום והזעות לילה סביב הפסקת המחזור.
ממצא תומך: שינוי בדפוסי הווסת בגיל המעבר.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **menopausal hot flashes** | chapters ['ch4'] → sections ['E08-E13'] (432 codes) → E08(86) → 86 cands → **NONE** (high)
  - gold N95.1 [matched dx: menopausal hot flashes]: Ch.14 Diseases of the genitourinary system (N00-N99) > Noninflammatory disorders of female genital tract (N80-N98) > N95 Menopausal and other perimenopausal disorders > N95.1 Menopausal and female climacteric states

### V0030  gold=['N63.11', 'N92.0']  pred=['N63.11', 'N99.0']
```
ביקור מרפאתי. בת 36.
תועד גם: המוגלובין ירד בהדרגה.
סיבת הפנייה: וסת סדירה אך כבדה מאוד עם קרישי דם.
בנוסף, נדונה בעיה נפרדת: גוש חדש ברביע העליון-חיצוני של שד ימין.
הנתונים הרלוונטיים לכך: הפניה להדמיה ובירור רקמתי לפי צורך.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **menorrhagia** | chapters ['ch14', 'ch14'] → sections ['N99', 'N30-N39'] (129 codes) → N99.0(1) → 1 cands → **N99.0** (low)
- **new right upper outer quadrant breast mass** | chapters ['ch14'] → sections ['N60-N65'] (60 codes) → 60 cands → **N63.11** (high)
  - gold N63.11 [matched dx: new right upper outer quadrant breast mass]: Ch.14 Diseases of the genitourinary system (N00-N99) > Disorders of breast (N60-N65) > N63 Unspecified lump in breast > N63.1 Unspecified lump in the right breast > N63.11 Unspecified lump in the right breast, upper outer quadrant
  - gold N92.0 [matched dx: menorrhagia]: Ch.14 Diseases of the genitourinary system (N00-N99) > Noninflammatory disorders of female genital tract (N80-N98) > N92 Excessive, frequent and irregular menstruation > N92.0 Excessive and frequent menstruation with regular cycle

### V0044  gold=['D75.1']  pred=['D64.2']
```
ביקור מרפאתי. בן 55.
בימים האחרונים דווח כי רמות המוגלובין והמטוקריט גבוהות בעישון ממושך.
ממצא תומך: אריתרופואטין מוגבר.
סוכם על תוכנית טיפול ומעקב בהתאם לבעיות שנדונו בביקור.
```
- **secondary polycythemia due to chronic smoking** | chapters ['ch3', 'ch1'] → sections ['D60-D64', 'B95-B97'] (75 codes) → 75 cands → **D64.2** (medium)
  - gold D75.1 [matched dx: secondary polycythemia due to chronic smoking]: Ch.3 Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism (D50-D89) > Other disorders of blood and blood-forming organs (D70-D77) > D75 Other and unspecified diseases of blood and blood-forming organs > D75.1 Secondary polycythemia

### V0045  gold=['N43.3']  pred=['N08']
```
ביקור מרפאתי. בן 56.
בהפניה מתוארת תמונה של נפיחות שק אשכים לא כואבת.
על פי המסמכים: באולטרסאונד נוזל סביב האשך.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **ascites** | chapters ['ch14'] → sections ['N00-N08'] (107 codes) → N08(1) → 1 cands → **N08** (medium)
  - gold N43.3 [matched dx: NONE]: Ch.14 Diseases of the genitourinary system (N00-N99) > Diseases of male genital organs (N40-N53) > N43 Hydrocele and spermatocele > N43.3 Hydrocele, unspecified

### V0048  gold=['A54.9', 'H91.92']  pred=[]
```
ביקור מרפאתי. בת 31.
בימים האחרונים דווח כי הפרשה וצריבה לאחר מגע מיני בלתי מוגן.
תועד גם: NAAT לגונוריאה חיובי.
תלונה נוספת שנבדקה: תלונה חדשה על שמיעה חלשה בצד שמאל.
לגבי הבעיה הנוספת נמצאו: נדרש בירור אודיולוגי נוסף.
סוכם על תוכנית טיפול ומעקב בהתאם לבעיות שנדונו בביקור.
```
- **gonorrhea** | chapters ['ch1'] → sections ['B95-B97'] (46 codes) → 46 cands → **NONE** (high)
- **sensorineural hearing loss, left ear** | chapters ['ch6'] → sections ['G40-G47'] (205 codes) → G40/G43/G44(146) → G40.0/G40.1/G40.2(12) → 12 cands → **NONE** (high)
  - gold A54.9 [matched dx: gonorrhea]: Ch.1 Certain infectious and parasitic diseases (A00-B99) > Infections with a predominantly sexual mode of transmission (A50-A64) > A54 Gonococcal infection > A54.9 Gonococcal infection, unspecified
  - gold H91.92 [matched dx: sensorineural hearing loss, left ear]: Ch.8 Diseases of the ear and mastoid process (H60-H95) > Other disorders of ear (H90-H94) > H91 Other and unspecified hearing loss > H91.9 Unspecified hearing loss > H91.92 Unspecified hearing loss, left ear

### V0052  gold=['D53.9', 'I22.9']  pred=['I21.9', 'E63.9', 'D53.8']
```
הערכה דחופה במוקד. בת 40.
מתאר/ת כי לאחר אוטם טרי הופיע אירוע כלילי חד נוסף.
ממצא תומך: עלייה מחודשת בטרופונין עם שינויים איסכמיים.
נושא נוסף שהועלה בביקור: חולשה בחולה עם תזונה מוגבלת ומדדי דם חריגים.
לגבי הבעיה הנוספת נמצאו: טרם זוהה רכיב התזונה החסר.
נרשם גם: אנמיה תזונתית לא מסווגת.
נדרשת הערכה וטיפול דחופים במסגרת מתאימה; תואמה הפניה מיידית.
```
- **acute myocardial infarction** | chapters ['ch9'] → sections ['I20-I25'] (94 codes) → 94 cands → **I21.9** (high)
- **unspecified nutritional deficiency** | chapters ['ch4'] → sections ['E50-E64'] (50 codes) → 50 cands → **E63.9** (high)
- **unspecified nutritional anemia** | chapters ['ch3'] → sections ['D50-D53'] (19 codes) → 19 cands → **D53.8** (high)
  - gold D53.9 [matched dx: unspecified nutritional anemia]: Ch.3 Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism (D50-D89) > Nutritional anemias (D50-D53) > D53 Other nutritional anemias > D53.9 Nutritional anemia, unspecified
  - gold I22.9 [matched dx: acute myocardial infarction]: Ch.9 Diseases of the circulatory system (I00-I99) > Ischemic heart diseases (I20-I25) > I22 Subsequent ST elevation (STEMI) and non-ST elevation (NSTEMI) myocardial infarction > I22.9 Subsequent ST elevation (STEMI) myocardial infarction of unspecified site

### V0057  gold=['H11.002']  pred=['H15.9']
```
ביקור מרפאתי. בן 27.
מתאר/ת כי תחושת גוף זר והפרעה קוסמטית בעין שמאל.
על פי המסמכים: פטריגיום נזלי נראה בבדיקה.
הערכה קלינית ראשונית: פטריגיום בעין שמאל.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **conjunctival pterygium of the left eye** | chapters ['ch7'] → sections ['H15-H22'] (497 codes) → H15(62) → 62 cands → **H15.9** (low)
  - gold H11.002 [matched dx: conjunctival pterygium of the left eye]: Ch.7 Diseases of the eye and adnexa (H00-H59) > Disorders of conjunctiva (H10-H11) > H11 Other disorders of conjunctiva > H11.0 Pterygium of eye > H11.00 Unspecified pterygium of eye > H11.002 Unspecified pterygium of left eye

### V0060  gold=['K56.609']  pred=['K52.831']
```
ביקור מרפאתי. בן 30.
מגיע/ה לבדיקה עקב הקאות חוזרות, נפיחות ואי מעבר גזים.
על פי המסמכים: צילום בטן עם לולאות מורחבות.
סוכם על תוכנית טיפול ומעקב בהתאם לבעיות שנדונו בביקור.
```
- **chronic diarrhea** | chapters ['ch11'] → sections ['K50-K52'] (91 codes) → 91 cands → **K52.831** (high)
  - gold K56.609 [matched dx: NONE]: Ch.11 Diseases of the digestive system (K00-K95) > Other diseases of intestines (K55-K64) > K56 Paralytic ileus and intestinal obstruction without hernia > K56.6 Other and unspecified intestinal obstruction > K56.60 Unspecified intestinal obstruction > K56.609 Unspecified intestinal obstruction, unspecified as to partial versus complete obstruction
# Evaluation report — test100_qwen35_9b: split=test, visits=100, gold codes=150 (majority ≥2/3)

## Final codes
- Exact code: P=0.431 R=0.500 F1=0.463
- 3-char category (lenient): P=0.588 R=0.667 F1=0.625
- Visit exact-set match: 0.340
- Precision vs ANY annotator: 0.448
- Predicted codes per visit: 1.74 (gold 1.50)

## Per-visit (multi-label) metrics
Micro P/R/F1 above pools all (visit, code) pairs; here every visit counts once.
- Per-visit average: P=0.484 R=0.532 F1=0.498 Jaccard=0.448
- Exact set match 0.34; all gold codes found 0.42; at least one found 0.66

| Gold codes in visit | Visits | Micro P / R / F1 | Per-visit F1 | Exact set match | Gold found: all / some / none (visits) | Codes predicted per visit |
|---|---|---|---|---|---|---|
| 1 | 58 | 0.486 / 0.586 / 0.531 | 0.543 | 0.47 | 34 / 0 / 24 | 1.21 |
| 2 | 34 | 0.418 / 0.485 / 0.449 | 0.456 | 0.21 | 8 / 17 / 9 | 2.32 |
| 3 | 8 | 0.320 / 0.333 / 0.327 | 0.342 | 0.00 | 0 / 7 / 1 | 3.12 |

## Human ceiling (pairwise annotator agreement, same visits)
- DR_A vs DR_B: P=0.916 R=0.979 F1=0.946
- DR_A vs DR_C: P=0.903 R=0.993 F1=0.946
- DR_B vs DR_C: P=0.917 R=0.943 F1=0.930

## Stage recalls (billable gold codes)
- Chapter Recall@3 (any diagnosis of the visit): 135/148 = 0.912
- Section Recall@3 (any diagnosis of the visit): 121/148 = 0.818
- Diagnosis extracted (matched by eval judge): 127/148 = 0.858
- Chapter recall given extracted: 118/127 = 0.929
- Section recall given extracted: 104/127 = 0.819
- Gold reached the final candidate list: 96/148 = 0.649
- Final choice correct when gold reached the final list: 70/96 = 0.729

## Where each gold code ends up (first failing stage)
- unreachable: gold code not billable in FY2027: 2 (1.3%)
- correct: 75 (50.0%)
- diagnosis never extracted: 19 (12.7%)
- extracted, wrong CHAPTER: 7 (4.7%)
- extracted, right chapter, wrong SECTION: 14 (9.3%)
- extracted, lost in CATEGORY/deeper narrowing: 8 (5.3%)
- reached final list, wrong FINAL choice: 25 (16.7%)

## False positives
- different category (extra/wrong diagnosis): 73
- same 3-char category as a gold code (granularity): 26

## Seen (code in dev gold) vs unseen
- seen: recall 18/37 = 0.486
- unseen: recall 57/111 = 0.514

## Validity & cost
- Valid billable codes: 174/174
- Evidence verbatim in note: 169/190 diagnoses (others snapped to the closest note line)
- Diagnoses extracted per visit: 1.90; NONE answers: 7
- Narrowing depth per diagnosis: {0: 65, 1: 104, 2: 21}
- Final candidate list size: mean 41.1, max 100
- Seconds/visit: 111.9; LLM calls/visit: 8.2

## Step-by-step details

### Path per extracted diagnosis (MAX_CODES = 100)
- Section → code directly (≤ 100 codes under the chosen sections): 65/190 (34%)
- Section → category (→ deeper) → code (> 100 codes): 125/190 (66%); narrowing levels used: {1: 104, 2: 21}
- Codes under the chosen sections — direct path: mean 65.1, median 67, max 100; narrowed path: mean 486.9, median 255, max 5010

### Options shown to the model at each step (per diagnosis)
- Chapter step: 22 options; chapters chosen: mean 1.9, median 2, max 3
- Section step: options mean 24.9, median 25, max 56; sections chosen: mean 1.6, median 2, max 3
- Category step (125 diagnoses): options mean 18.2, median 17, max 42; codes left after it mean 69.0, median 28, max 729
- Deeper level 2 (21 diagnoses): options mean 14.7, median 15, max 21; codes left after it mean 29.4, median 27, max 65
- Final code step: candidates mean 41.1, median 35, max 100 (direct path mean 65.1, median 67, max 100; narrowed path mean 28.6, median 23, max 96)

### Step accuracy (gold codes whose diagnosis was extracted; each step given the previous one was right)
- Chapter: gold chapter among chosen chapters: 118/127 = 0.929
- Section: gold section among chosen sections | chapter right: 104/118 = 0.881
- Category: gold category kept at the category step | section right & narrowing ran: 51/58 = 0.879
- Narrowing overall: gold still in final candidates | section right & narrowing ran: 50/58 = 0.862
- Code: correct final code | gold in candidates: 70/96 = 0.729 (direct path 35/46 = 0.761; narrowed path 35/50 = 0.700)
- End to end, for extracted diagnoses: 70/127 = 0.551

### Confidence (final step only; no threshold is applied by the system)
- high (0.9): 158 codes, precision 0.437
- medium (0.6): 16 codes, precision 0.375
- If only codes with score ≥ 0.3 were returned: P=0.431 R=0.500 F1=0.463
- If only codes with score ≥ 0.6 were returned: P=0.431 R=0.500 F1=0.463
- If only codes with score ≥ 0.9 were returned: P=0.437 R=0.460 F1=0.448

## Failure examples

### V0003  gold=['E29.1', 'F25.9']  pred=['F29', 'E29.1']
```
ביקור מרפאתי. בת 67.
סיבת הפנייה: תסמיני פסיכוזה לצד פרקים אפקטיביים משמעותיים.
בבדיקה: נדרשת תוכנית טיפול פסיכיאטרית רציפה.
נושא נוסף שהועלה בביקור: ירידה בחשק המיני ועייפות לאורך זמן.
הממצא המחזק את התלונה הנוספת: טסטוסטרון בוקר נמוך בשתי מדידות.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **Psychotic disorder with significant affective episodes** | chapters ['ch5', 'ch18'] → sections ['F20-F29', 'F30-F39'] (80 codes) → 80 cands → **F29** (high)
- **Hypogonadism** | chapters ['ch4', 'ch14'] → sections ['E20-E35'] (99 codes) → 99 cands → **E29.1** (high)
  - gold E29.1 [matched dx: Hypogonadism]: Ch.4 Endocrine, nutritional and metabolic diseases (E00-E89) > Disorders of other endocrine glands (E20-E35) > E29 Testicular dysfunction > E29.1 Testicular hypofunction
  - gold F25.9 [matched dx: Psychotic disorder with significant affective episodes]: Ch.5 Mental, Behavioral and Neurodevelopmental disorders (F01-F99) > Schizophrenia, schizotypal, delusional, and other non-mood psychotic disorders (F20-F29) > F25 Schizoaffective disorders > F25.9 Schizoaffective disorder, unspecified

### V0011  gold=['J00', 'J40']  pred=['J00', 'R05.9', 'R06.2', 'J02.9']
```
ביקור מרפאתי. בת 53.
ממצא תומך: ללא חום גבוה או סימני זיהום חיידקי.
מהשיחה ומהתיק: נזלת מימית עם כאב גרון קל מספר ימים.
בסקירת מצב בריאותי נוסף עלה כי שיעול ליחתי שאינו עונה בבירור על משך ברונכיטיס כרונית.
לגבי הבעיה הנוספת נמצאו: בהאזנה חרחורים גסים מפוזרים.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **Acute rhinitis** | chapters ['ch10'] → sections ['J00-J06'] (35 codes) → 35 cands → **J00** (high)
- **Acute pharyngitis** | chapters ['ch10', 'ch18'] → sections ['J00-J06'] (35 codes) → 35 cands → **J02.9** (medium)
- **Cough, unspecified** | chapters ['ch10', 'ch18'] → sections ['R00-R09', 'J30-J39', 'J20-J22'] (140 codes) → R05/R07/J30(20) → 20 cands → **R05.9** (high)
- **Wheezing** | chapters ['ch10', 'ch18'] → sections ['R00-R09', 'J40-J4B', 'J30-J39'] (165 codes) → R06/R05/J30(30) → 30 cands → **R06.2** (high)
  - gold J00 [matched dx: Acute rhinitis]: Ch.10 Diseases of the respiratory system (J00-J99) > Acute upper respiratory infections (J00-J06) > J00 Acute nasopharyngitis [common cold]
  - gold J40 [matched dx: Cough, unspecified]: Ch.10 Diseases of the respiratory system (J00-J99) > Chronic lower respiratory diseases (J40-J4B) > J40 Bronchitis, not specified as acute or chronic

### V0014  gold=['I73.9']  pred=['I70.219', 'I73.89']
```
ביקור מרפאתי. בן 81.
בהפניה מתוארת תמונה של רגליים קרות וכאבי מאמץ עם חשד להפרעה בזרימה.
על פי המסמכים: ABI מופחת.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **Peripheral arterial disease** | chapters ['ch9'] → sections ['I70-I79'] (344 codes) → I70/I73(252) → I70.2(40) → 40 cands → **I70.219** (high)
- **Decreased ankle-brachial index** | chapters ['ch9', 'ch18'] → sections ['I70-I79', 'R00-R09'] (402 codes) → I73/I77(29) → 29 cands → **I73.89** (high)
  - gold I73.9 [matched dx: Peripheral arterial disease]: Ch.9 Diseases of the circulatory system (I00-I99) > Diseases of arteries, arterioles and capillaries (I70-I79) > I73 Other peripheral vascular diseases > I73.9 Peripheral vascular disease, unspecified

### V0015  gold=['F80.9', 'L28.0']  pred=['F80.9', 'L20.9']
```
ביקור מרפאתי לילד/ה בגיל 12 בליווי הורה.
מהשיחה ומהתיק: עיכוב בדיבור ביחס לבני גילו ללא אבחנה מלאה.
ממצא תומך: הופנה לאבחון שפה מקיף.
הערכה קלינית ראשונית: הפרעה התפתחותית בשפה ובדיבור לא מסווגת.
בסקירת מצב בריאותי נוסף עלה כי רובד מעובה ומגרד בעור לאחר שפשוף חוזר.
הנתונים הרלוונטיים לכך: הדגשת קווי העור.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **Developmental language disorder, unspecified** | chapters ['ch5', 'ch18'] → sections ['F80-F89'] (22 codes) → 22 cands → **F80.9** (high)
- **Atopic dermatitis** | chapters ['ch12', 'ch5'] → sections ['L20-L30'] (74 codes) → 74 cands → **L20.9** (high)
  - gold F80.9 [matched dx: Developmental language disorder, unspecified]: Ch.5 Mental, Behavioral and Neurodevelopmental disorders (F01-F99) > Pervasive and specific developmental disorders (F80-F89) > F80 Specific developmental disorders of speech and language > F80.9 Developmental disorder of speech and language, unspecified
  - gold L28.0 [matched dx: Atopic dermatitis]: Ch.12 Diseases of the skin and subcutaneous tissue (L00-L99) > Dermatitis and eczema (L20-L30) > L28 Lichen simplex chronicus and prurigo > L28.0 Lichen simplex chronicus

### V0016  gold=['J05.0']  pred=['R06.2', 'R05.9']
```
ביקור מרפאתי. בת 15.
ממצא תומך: סטרידור שאיפתי קל במנוחה.
לדברי המטופל/ת, שיעול נבחני וצרידות בילד בלילה.
המידע הושווה לתיעוד הרפואי הקודם.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **Wheezing** | chapters ['ch10', 'ch18'] → sections ['R00-R09', 'J40-J4B', 'J30-J39'] (165 codes) → R06/R05/R09(35) → 35 cands → **R06.2** (high)
- **Cough** | chapters ['ch10', 'ch18'] → sections ['R00-R09', 'J30-J39', 'J00-J06'] (160 codes) → R05/R07/J39(19) → 19 cands → **R05.9** (high)
  - gold J05.0 [matched dx: Wheezing]: Ch.10 Diseases of the respiratory system (J00-J99) > Acute upper respiratory infections (J00-J06) > J05 Acute obstructive laryngitis [croup] and epiglottitis > J05.0 Acute obstructive laryngitis [croup]

### V0018  gold=['E29.1', 'E87.5', 'F41.1']  pred=['F41.9', 'G47.9', 'R79.0', 'F52.0', 'N19']
```
ביקור מרפאתי. בת 74.
סיבת הפנייה: דאגנות בלתי נשלטת בנושאים רבים במשך חודשים.
ממצא תומך: מתח שרירי והפרעת שינה.
תלונה נוספת שנבדקה: חולשת שרירים במטופל עם הפרעת תפקוד כליות.
לגבי הבעיה הנוספת נמצאו: אשלגן 6.2 ושינויים באקג.
בסקירת מצב בריאותי נוסף עלה כי ירידה בחשק המיני ועייפות לאורך זמן.
הנתונים הרלוונטיים לכך: טסטוסטרון בוקר נמוך בשתי מדידות.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **Uncontrolled anxiety** | chapters ['ch5', 'ch18'] → sections ['F40-F48', 'R40-R46'] (228 codes) → F41/R45(23) → 23 cands → **F41.9** (high)
- **Muscle tension and sleep disorder** | chapters ['ch5', 'ch6', 'ch18'] → sections ['G40-G47', 'R40-R46'] (362 codes) → G47(43) → 43 cands → **G47.9** (high)
- **Renal insufficiency** | chapters ['ch14', 'ch6', 'ch5'] → sections ['N17-N19', 'N25-N29'] (37 codes) → 37 cands → **N19** (medium)
- **Hyperkalemia** | chapters ['ch18', 'ch9'] → sections ['R70-R79'] (45 codes) → 45 cands → **R79.0** (high)
- **Hypotension** | chapters ['ch9', 'ch18'] → sections ['I95-I99'] (49 codes) → 49 cands → **NONE** (high)
- **Hypoactive sexual desire disorder** | chapters ['ch5', 'ch18'] → sections ['F50-F59'] (66 codes) → 66 cands → **F52.0** (high)
  - gold E29.1 [matched dx: Hypoactive sexual desire disorder]: Ch.4 Endocrine, nutritional and metabolic diseases (E00-E89) > Disorders of other endocrine glands (E20-E35) > E29 Testicular dysfunction > E29.1 Testicular hypofunction
  - gold E87.5 [matched dx: Hyperkalemia]: Ch.4 Endocrine, nutritional and metabolic diseases (E00-E89) > Metabolic disorders (E70-E88) > E87 Other disorders of fluid, electrolyte and acid-base balance > E87.5 Hyperkalemia
  - gold F41.1 [matched dx: Uncontrolled anxiety]: Ch.5 Mental, Behavioral and Neurodevelopmental disorders (F01-F99) > Anxiety, dissociative, stress-related, somatoform and other nonpsychotic mental disorders (F40-F48) > F41 Other anxiety disorders > F41.1 Generalized anxiety disorder

### V0019  gold=['E11.22', 'L82.1']  pred=['B08.1', 'E11.21']
```
ביקור מרפאתי. בן 59.
מתאר/ת כי נגע חום שנראה מודבק על פני העור.
בדיקות וממצאים: מראה שעוותי וגבולות ברורים.
בנוסף, נדונה בעיה נפרדת: סוכרת ממושכת עם אלבומינוריה וירידה בתפקוד הכלייתי.
לגבי הבעיה הנוספת נמצאו: יחס אלבומין לקריאטינין מוגבר לאורך זמן.
לא הועלתה תלונה חריפה נוספת מעבר לנושאים שנדונו.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **Warts** | chapters ['ch1', 'ch12'] → sections ['B00-B09', 'L80-L99'] (633 codes) → B07/B08(25) → 25 cands → **B08.1** (high)
- **Diabetes mellitus with albuminuria and decreased renal function** | chapters ['ch4', 'ch14'] → sections ['E08-E13', 'N17-N19'] (447 codes) → E11/N18(96) → 96 cands → **E11.21** (high)
  - gold E11.22 [matched dx: Warts]: Ch.4 Endocrine, nutritional and metabolic diseases (E00-E89) > Diabetes mellitus (E08-E13) > E11 Type 2 diabetes mellitus > E11.2 Type 2 diabetes mellitus with kidney complications > E11.22 Type 2 diabetes mellitus with diabetic chronic kidney disease
  - gold L82.1 [matched dx: Warts]: Ch.12 Diseases of the skin and subcutaneous tissue (L00-L99) > Other disorders of the skin and subcutaneous tissue (L80-L99) > L82 Seborrheic keratosis > L82.1 Other seborrheic keratosis

### V0022  gold=['M77.12', 'S53.401A']  pred=['S53.401A', 'M67.824']
```
הערכה דחופה במוקד. בת 84.
לדברי המטופל/ת, כאב ונפיחות במרפק ימין לאחר נפילה.
בדיקות וממצאים: צילום ללא שבר וללא פריקה.
הערכה קלינית ראשונית: נקע לא מסווג במרפק ימין.
נושא נוסף שהועלה בביקור: כאב לטרלי במרפק שמאל לאחר עבודה עם כלי עבודה.
הממצא המחזק את התלונה הנוספת: רגישות באפיקונדיל הלטרלי.
המטופל/ת דיווח/ה על תפקוד עצמאי בבית.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **Unspecified sprain of right elbow, initial encounter** | chapters ['ch13', 'ch19'] → sections ['S50-S59'] (4362 codes) → S53/S59(621) → S53.4(54) → 54 cands → **S53.401A** (high)
- **Lateral epicondylitis of left elbow** | chapters ['ch13', 'ch19'] → sections ['M65-M67'] (379 codes) → M65/M67(276) → M67.8(38) → 38 cands → **M67.824** (high)
  - gold M77.12 [matched dx: Lateral epicondylitis of left elbow]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Other soft tissue disorders (M70-M79) > M77 Other enthesopathies > M77.1 Lateral epicondylitis > M77.12 Lateral epicondylitis, left elbow
  - gold S53.401A [matched dx: Unspecified sprain of right elbow, initial encounter]: Ch.19 Injury, poisoning and certain other consequences of external causes (S00-T88) > Injuries to the elbow and forearm (S50-S59) > S53 Dislocation and sprain of joints and ligaments of elbow > S53.4 Sprain of elbow > S53.40 Unspecified sprain of elbow > S53.401 Unspecified sprain of right elbow > S53.401A Unspecified sprain of right elbow, initial encounter

### V0023  gold=['P92.9']  pred=['R62.51']
```
ביקור מרפאתי לילד/ה בגיל 5 בליווי הורה.
סיבת הפנייה: תינוק בן ימים מתקשה לינוק ועולה במשקל לאט.
ממצא תומך: האכלה קצרה ונדרשת הערכת יועצת הנקה.
המטופל/ת דיווח/ה על תפקוד עצמאי בבית.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **Failure to thrive** | chapters ['ch4', 'ch18', 'ch21'] → sections ['E40-E46', 'R50-R69'] (76 codes) → 76 cands → **R62.51** (high)
  - gold P92.9 [matched dx: NONE]: Ch.16 Certain conditions originating in the perinatal period (P00-P96) > Other disorders originating in the perinatal period (P90-P96) > P92 Feeding problems of newborn > P92.9 Feeding problem of newborn, unspecified

### V0027  gold=['R76.8']  pred=['R76.89']
```
ביקור מרפאתי. בן 74.
סיבת הפנייה: נוגדנים עצמיים חיוביים ללא מחלה קלינית מאובחנת.
על פי המסמכים: אין מפרקים נפוחים או קריטריונים למחלה מוגדרת.
הערכה קלינית ראשונית: ממצאים אימונולוגיים חריגים אחרים בדם.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **Positive autoantibodies without clinical disease** | chapters ['ch3', 'ch18'] → sections ['D80-D89', 'R70-R79'] (128 codes) → R76(6) → 6 cands → **R76.89** (high)
  - gold R76.8 [matched dx: Positive autoantibodies without clinical disease]: Ch.18 Symptoms, signs and abnormal clinical and laboratory findings, not elsewhere classified (R00-R99) > Abnormal findings on examination of blood, without diagnosis (R70-R79) > R76 Other abnormal immunological findings in serum > R76.8 Other specified abnormal immunological findings in serum

### V0033  gold=['N30.00']  pred=['N30.90', 'R30.0']
```
ביקור מרפאתי. בן 51.
בימים האחרונים דווח כי צריבה ודחיפות בהשתנה ללא חום.
תועד גם: לויקוציטים בבדיקת שתן ללא סימני פיאלונפריטיס.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **Acute cystitis** | chapters ['ch14', 'ch18'] → sections ['N30-N39'] (85 codes) → 85 cands → **N30.90** (high)
- **Urinary tract infection** | chapters ['ch14', 'ch18'] → sections ['N30-N39', 'R30-R39'] (127 codes) → N30/N34/R30(21) → 21 cands → **R30.0** (high)
  - gold N30.00 [matched dx: Acute cystitis]: Ch.14 Diseases of the genitourinary system (N00-N99) > Other diseases of the urinary system (N30-N39) > N30 Cystitis > N30.0 Acute cystitis > N30.00 Acute cystitis without hematuria

### V0026  gold=['M19.012', 'M21.41', 'M79.672']  pred=['M25.572', 'M79.671', 'M19.012']
```
ביקור מרפאתי. בת 83.
בימים האחרונים דווח כי כאב בעצמות המסרק בכף רגל שמאל לאחר הליכה.
בדיקות וממצאים: ללא ממצא חד בהדמיה.
הערכה קלינית ראשונית: כאב בכף רגל שמאל.
תלונה נוספת שנבדקה: כאבי קשת כף רגל ימין בהליכה ממושכת.
הממצא המחזק את התלונה הנוספת: ירידה בקשת האורכית בעמידה.
בסקירת מצב בריאותי נוסף עלה כי כאב עמום בכתף שמאל בזמן תנועות יומיומיות.
הנתונים הרלוונטיים לכך: קרפיטוס בתנועות וסימני שחיקה.
נרשם גם: אוסטאוארתריטיס ראשונית של כתף שמאל.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **Left foot pain** | chapters ['ch13', 'ch18'] → sections ['M20-M25', 'M70-M79', 'R50-R69'] (1145 codes) → M25/M79(277) → M25.5/M79.6(54) → 54 cands → **M25.572** (high)
- **Right foot pain** | chapters ['ch13', 'ch18'] → sections ['M70-M79'] (358 codes) → M79(52) → 52 cands → **M79.671** (high)
- **Primary osteoarthritis of left shoulder** | chapters ['ch13'] → sections ['M15-M19'] (98 codes) → 98 cands → **M19.012** (high)
  - gold M19.012 [matched dx: Primary osteoarthritis of left shoulder]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Osteoarthritis (M15-M19) > M19 Other and unspecified osteoarthritis > M19.0 Primary osteoarthritis of other joints > M19.01 Primary osteoarthritis, shoulder > M19.012 Primary osteoarthritis, left shoulder
  - gold M21.41 [matched dx: Right foot pain]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Other joint disorders (M20-M25) > M21 Other acquired deformities of limbs > M21.4 Flat foot [pes planus] (acquired) > M21.41 Flat foot [pes planus] (acquired), right foot
  - gold M79.672 [matched dx: Left foot pain]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Other soft tissue disorders (M70-M79) > M79 Other and unspecified soft tissue disorders, not elsewhere classified > M79.6 Pain in limb, hand, foot, fingers and toes > M79.67 Pain in foot and toes > M79.672 Pain in left foot

### V0025  gold=['M16.11']  pred=['M25.561', 'M25.651', 'M16.11']
```
ביקור מרפאתי. בת 62.
לדברי המטופל/ת, כאבים במפשעה ובירך ימין בעלייה במדרגות.
על פי המסמכים: טווח סיבוב פנימי מוגבל ושינויים ניווניים בצילום.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **Right hip and knee pain** | chapters ['ch13', 'ch18'] → sections ['M15-M19', 'M20-M25', 'M70-M79'] (1175 codes) → M25/M16(240) → M25.5/M25.7/M16.9(50) → 50 cands → **M25.561** (high)
- **Limited internal rotation of the right hip** | chapters ['ch13', 'ch18'] → sections ['M20-M25', 'M15-M19'] (817 codes) → M25/M16(240) → M25.6/M25.7(52) → 52 cands → **M25.651** (high)
- **Osteoarthritis of the right hip and knee** | chapters ['ch13'] → sections ['M15-M19'] (98 codes) → 98 cands → **M16.11** (high)
  - gold M16.11 [matched dx: Osteoarthritis of the right hip and knee]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Osteoarthritis (M15-M19) > M16 Osteoarthritis of hip > M16.1 Unilateral primary osteoarthritis of hip > M16.11 Unilateral primary osteoarthritis, right hip

### V0032  gold=['M72.2', 'M76.62']  pred=['M77.52', 'M67.874']
```
ביקור מרפאתי. בת 70.
מגיע/ה לבדיקה עקב כאב בעקב בצעדים הראשונים בבוקר.
תועד גם: רגישות בחיבור הפציה הפלנטרית.
בסקירת מצב בריאותי נוסף עלה כי כאב בצד שמאל מאחורי העקב אחרי אימון קפיצות.
הנתונים הרלוונטיים לכך: רגישות בגיד ללא קרע.
נרשם גם: אכילס טנדיניטיס ברגל שמאל.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **Plantar fasciitis, left foot** | chapters ['ch13', 'ch18'] → sections ['M65-M67', 'M70-M79'] (737 codes) → M77(20) → 20 cands → **M77.52** (high)
- **Achilles tendinitis, left foot** | chapters ['ch13', 'ch18', 'ch19'] → sections ['M65-M67'] (379 codes) → M65/M67(276) → M67.8/M67.0/M67.9(65) → 65 cands → **M67.874** (high)
  - gold M72.2 [matched dx: NONE]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Other soft tissue disorders (M70-M79) > M72 Fibroblastic disorders > M72.2 Plantar fascial fibromatosis
  - gold M76.62 [matched dx: Achilles tendinitis, left foot]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Other soft tissue disorders (M70-M79) > M76 Enthesopathies, lower limb, excluding foot > M76.6 Achilles tendinitis > M76.62 Achilles tendinitis, left leg

### V0038  gold=['Z01.810']  pred=[]
```
ביקור מרפאתי. בת 29.
לדברי המטופל/ת, הערכה לבבית טרום ניתוח מתוכנן.
בבדיקה: אין תסמינים קרדיאליים פעילים.
הערכה קלינית ראשונית: בדיקה קרדיווסקולרית לקראת פרוצדורה.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
  - gold Z01.810 [matched dx: NONE]: Ch.21 Factors influencing health status and contact with health services (Z00-Z99) > Persons encountering health services for examinations (Z00-Z13) > Z01 Encounter for other special examination without complaint, suspected or reported diagnosis > Z01.8 Encounter for other specified special examinations > Z01.81 Encounter for preprocedural examinations > Z01.810 Encounter for preprocedural cardiovascular examination
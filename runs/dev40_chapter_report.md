# Evaluation report — dev40_chapter: split=dev, visits=40, gold codes=60 (majority ≥2/3)

## Final codes
- Exact code: P=0.305 R=0.300 F1=0.303
- 3-char category (lenient): P=0.458 R=0.450 F1=0.454
- Visit exact-set match: 0.175
- Precision vs ANY annotator: 0.305
- Predicted codes per visit: 1.48 (gold 1.50)

## Per-visit (multi-label) metrics
Micro P/R/F1 above pools all (visit, code) pairs; here every visit counts once.
- Per-visit average: P=0.265 R=0.267 F1=0.265 Jaccard=0.233
- Exact set match 0.17; all gold codes found 0.17; at least one found 0.38

| Gold codes in visit | Visits | Micro P / R / F1 | Per-visit F1 | Exact set match | Gold found: all / some / none (visits) | Codes predicted per visit |
|---|---|---|---|---|---|---|
| 1 | 23 | 0.263 / 0.217 / 0.238 | 0.217 | 0.22 | 5 / 0 / 18 | 0.83 |
| 2 | 14 | 0.258 / 0.286 / 0.271 | 0.279 | 0.07 | 1 / 6 / 7 | 2.21 |
| 3 | 3 | 0.556 / 0.556 / 0.556 | 0.562 | 0.33 | 1 / 2 / 0 | 3.00 |

## Human ceiling (pairwise annotator agreement, same visits)
- DR_A vs DR_B: P=1.000 R=0.967 F1=0.983
- DR_A vs DR_C: P=0.914 R=0.964 F1=0.938
- DR_B vs DR_C: P=0.917 R=1.000 F1=0.957

## Stage recalls (billable gold codes)
- Chapter Recall@3 (any diagnosis of the visit): 51/60 = 0.850
- Section Recall@3 (any diagnosis of the visit): 36/60 = 0.600
- Diagnosis extracted (matched by eval judge): 45/60 = 0.750
- Chapter recall given extracted: 39/45 = 0.867
- Section recall given extracted: 30/45 = 0.667
- Gold reached the final candidate list: 25/60 = 0.417
- Final choice correct when gold reached the final list: 17/25 = 0.680

## Where each gold code ends up (first failing stage)
- correct: 18 (30.0%)
- diagnosis never extracted: 15 (25.0%)
- extracted, wrong CHAPTER: 5 (8.3%)
- extracted, right chapter, wrong SECTION: 9 (15.0%)
- extracted, lost in CATEGORY/deeper narrowing: 5 (8.3%)
- reached final list, wrong FINAL choice: 8 (13.3%)

## False positives
- different category (extra/wrong diagnosis): 32
- same 3-char category as a gold code (granularity): 9

## Validity & cost
- Valid billable codes: 59/59
- Evidence verbatim in note: 60/70 diagnoses (others snapped to the closest note line)
- Diagnoses extracted per visit: 1.75; NONE answers: 9
- Narrowing depth per diagnosis: {0: 28, 1: 34, 2: 8}
- Final candidate list size: mean 42.5, max 99
- Seconds/visit: 17.5; LLM calls/visit: 7.5

## Step-by-step details

### Path per extracted diagnosis (MAX_CODES = 100)
- Section → code directly (≤ 100 codes under the chosen sections): 28/70 (40%)
- Section → category (→ deeper) → code (> 100 codes): 42/70 (60%); narrowing levels used: {1: 34, 2: 8}
- Codes under the chosen sections — direct path: mean 62.1, median 67, max 99; narrowed path: mean 413.8, median 286, max 1611

### Options shown to the model at each step (per diagnosis)
- Chapter step: 22 options; chapters chosen: mean 1.5, median 1, max 3
- Section step: options mean 18.0, median 15, max 47; sections chosen: mean 1.6, median 1, max 3
- Category step (42 diagnoses): options mean 17.0, median 17, max 46; codes left after it mean 60.3, median 34, max 262
- Deeper level 2 (8 diagnoses): options mean 10.8, median 11, max 20; codes left after it mean 15.0, median 3, max 86
- Final code step: candidates mean 42.5, median 34, max 99 (direct path mean 62.1, median 67, max 99; narrowed path mean 29.5, median 23, max 87)

### Step accuracy (gold codes whose diagnosis was extracted; each step given the previous one was right)
- Chapter: gold chapter among chosen chapters: 39/45 = 0.867
- Section: gold section among chosen sections | chapter right: 30/39 = 0.769
- Category: gold category kept at the category step | section right & narrowing ran: 13/16 = 0.812
- Narrowing overall: gold still in final candidates | section right & narrowing ran: 11/16 = 0.688
- Code: correct final code | gold in candidates: 17/25 = 0.680 (direct path 10/14 = 0.714; narrowed path 7/11 = 0.636)
- End to end, for extracted diagnoses: 17/45 = 0.378

### Confidence (final step only; no threshold is applied by the system)
- high (0.9): 57 codes, precision 0.316
- medium (0.6): 2 codes, precision 0.000
- If only codes with score ≥ 0.3 were returned: P=0.305 R=0.300 F1=0.303
- If only codes with score ≥ 0.6 were returned: P=0.305 R=0.300 F1=0.303
- If only codes with score ≥ 0.9 were returned: P=0.316 R=0.300 F1=0.308

## Failure examples

### V0008  gold=['E87.6', 'L25.9']  pred=['L25.9', 'R29.91']
```
ביקור מרפאתי. בן 35.
תועד גם: אריתמה וקילוף באזור החשיפה.
מהשיחה ומהתיק: פריחה אחרי חשיפה לחומר חדש, טרם סווג המנגנון.
הערכה קלינית ראשונית: דרמטיטיס ממגע לא מסווגת.
בנוסף, נדונה בעיה נפרדת: חולשה והתכווצויות לאחר הקאות מרובות.
הממצא המחזק את התלונה הנוספת: אשלגן 2.9.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **contact dermatitis, unspecified** | chapters ['ch12'] → sections ['L20-L30'] (74 codes) → 74 cands → **L25.9** (high)
- **muscle weakness and cramps after multiple bowel movements** | chapters ['ch13', 'ch18'] → sections ['M60-M63', 'R25-R29', 'R50-R69'] (560 codes) → R29(57) → 57 cands → **R29.91** (medium)
- **hypokalemia** | chapters ['ch14'] → sections ['N25-N29'] (22 codes) → 22 cands → **NONE** (high)
  - gold E87.6 [matched dx: hypokalemia]: Ch.4 Endocrine, nutritional and metabolic diseases (E00-E89) > Metabolic disorders (E70-E88) > E87 Other disorders of fluid, electrolyte and acid-base balance > E87.6 Hypokalemia
  - gold L25.9 [matched dx: contact dermatitis, unspecified]: Ch.12 Diseases of the skin and subcutaneous tissue (L00-L99) > Dermatitis and eczema (L20-L30) > L25 Unspecified contact dermatitis > L25.9 Unspecified contact dermatitis, unspecified cause

### V0009  gold=['H61.21']  pred=['H60.331']
```
ביקור מרפאתי. בן 68.
בהפניה מתוארת תמונה של ירידה פתאומית בשמיעה באוזן ימין ללא כאב.
בדיקות וממצאים: פקק צרומן מסתיר עור התוף.
הערכה קלינית ראשונית: פקק שעווה באוזן ימין.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **acute otitis externa of right ear** | chapters ['ch8'] → sections ['H60-H62'] (144 codes) → H60(72) → 72 cands → **H60.331** (high)
  - gold H61.21 [matched dx: NONE]: Ch.8 Diseases of the ear and mastoid process (H60-H95) > Diseases of external ear (H60-H62) > H61 Other disorders of external ear > H61.2 Impacted cerumen > H61.21 Impacted cerumen, right ear

### V0010  gold=['M05.79', 'M79.7']  pred=['M05.A', 'R53.81']
```
ביקור מרפאתי. בן 70.
בהפניה מתוארת תמונה של נפיחות סימטרית במפרקי אצבעות עם נוקשות בוקר ארוכה.
תועד גם: RF ו-anti-CCP חיוביים.
בנוסף, נדונה בעיה נפרדת: כאב מפושט, שינה לא מרעננת וקשיי ריכוז.
הממצא המחזק את התלונה הנוספת: רגישות נרחבת ללא דלקת מפרקים בבדיקה.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **symmetric hand swelling with morning stiffness** | chapters ['ch13', 'ch18'] → sections ['M05-M14', 'R47-R49', 'R50-R69'] (1272 codes) → M05(211) → M05.A(1) → 1 cands → **M05.A** (high)
- **rheumatoid arthritis** | chapters ['ch13', 'ch3'] → sections ['M05-M14'] (1185 codes) → M05(211) → M05.A(1) → 1 cands → **M05.A** (high)
- **widespread hypersensitivity without joint inflammation** | chapters ['ch3', 'ch18'] → sections ['R25-R29', 'R50-R69', 'R20-R23'] (166 codes) → R52/R53/R60(10) → 10 cands → **R53.81** (high)
  - gold M05.79 [matched dx: rheumatoid arthritis]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Inflammatory polyarthropathies (M05-M14) > M05 Rheumatoid arthritis with rheumatoid factor > M05.7 Rheumatoid arthritis with rheumatoid factor without organ or systems involvement > M05.79 Rheumatoid arthritis with rheumatoid factor of multiple sites without organ or systems involvement
  - gold M79.7 [matched dx: NONE]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Other soft tissue disorders (M70-M79) > M79 Other and unspecified soft tissue disorders, not elsewhere classified > M79.7 Fibromyalgia

### V0013  gold=['G56.02', 'H25.11']  pred=['H25.011', 'G56.02']
```
ביקור מרפאתי. בן 60.
בבדיקה: עכירות גרעינית של העדשה.
בהפניה מתוארת תמונה של טשטוש ראייה מתקדם וסנוור בלילה בעין ימין.
הערכה קלינית ראשונית: קטרקט גרעיני תלוי גיל בעין ימין.
בנוסף, נדונה בעיה נפרדת: כאב ותחושת זרמים בכף יד שמאל בעת נהיגה.
הממצא המחזק את התלונה הנוספת: EMG מתאים ללחץ על העצב המדיאני משמאל.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **cataract, age-related, right eye** | chapters ['ch7'] → sections ['H25-H28'] (119 codes) → H25(30) → 30 cands → **H25.011** (high)
- **median nerve compression, left upper extremity** | chapters ['ch6', 'ch13'] → sections ['G50-G59'] (106 codes) → G56(28) → 28 cands → **G56.02** (high)
  - gold G56.02 [matched dx: cataract, age-related, right eye]: Ch.6 Diseases of the nervous system (G00-G99) > Nerve, nerve root and plexus disorders (G50-G59) > G56 Mononeuropathies of upper limb > G56.0 Carpal tunnel syndrome > G56.02 Carpal tunnel syndrome, left upper limb
  - gold H25.11 [matched dx: cataract, age-related, right eye]: Ch.7 Diseases of the eye and adnexa (H00-H59) > Disorders of lens (H25-H28) > H25 Age-related cataract > H25.1 Age-related nuclear cataract > H25.11 Age-related nuclear cataract, right eye

### V0024  gold=['N95.1']  pred=['E28.310']
```
ביקור מרפאתי. בת 70.
בהפניה מתוארת תמונה של גלי חום והזעות לילה סביב הפסקת המחזור.
ממצא תומך: שינוי בדפוסי הווסת בגיל המעבר.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **menopausal hot flashes** | chapters ['ch4'] → sections ['E20-E35'] (99 codes) → 99 cands → **E28.310** (high)
  - gold N95.1 [matched dx: menopausal hot flashes]: Ch.14 Diseases of the genitourinary system (N00-N99) > Noninflammatory disorders of female genital tract (N80-N98) > N95 Menopausal and other perimenopausal disorders > N95.1 Menopausal and female climacteric states

### V0044  gold=['D75.1']  pred=[]
```
ביקור מרפאתי. בן 55.
בימים האחרונים דווח כי רמות המוגלובין והמטוקריט גבוהות בעישון ממושך.
ממצא תומך: אריתרופואטין מוגבר.
סוכם על תוכנית טיפול ומעקב בהתאם לבעיות שנדונו בביקור.
```
- **secondary polycythemia due to chronic smoking** | chapters ['ch3'] → sections ['D60-D64'] (29 codes) → 29 cands → **NONE** (high)
  - gold D75.1 [matched dx: secondary polycythemia due to chronic smoking]: Ch.3 Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism (D50-D89) > Other disorders of blood and blood-forming organs (D70-D77) > D75 Other and unspecified diseases of blood and blood-forming organs > D75.1 Secondary polycythemia

### V0045  gold=['N43.3']  pred=[]
```
ביקור מרפאתי. בן 56.
בהפניה מתוארת תמונה של נפיחות שק אשכים לא כואבת.
על פי המסמכים: באולטרסאונד נוזל סביב האשך.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **ascites** | chapters ['ch14', 'ch18'] → sections ['R10-R19', 'R30-R39', 'R50-R69'] (209 codes) → R17(1) → 1 cands → **NONE** (high)
  - gold N43.3 [matched dx: NONE]: Ch.14 Diseases of the genitourinary system (N00-N99) > Diseases of male genital organs (N40-N53) > N43 Hydrocele and spermatocele > N43.3 Hydrocele, unspecified

### V0048  gold=['A54.9', 'H91.92']  pred=['H90.42']
```
ביקור מרפאתי. בת 31.
בימים האחרונים דווח כי הפרשה וצריבה לאחר מגע מיני בלתי מוגן.
תועד גם: NAAT לגונוריאה חיובי.
תלונה נוספת שנבדקה: תלונה חדשה על שמיעה חלשה בצד שמאל.
לגבי הבעיה הנוספת נמצאו: נדרש בירור אודיולוגי נוסף.
סוכם על תוכנית טיפול ומעקב בהתאם לבעיות שנדונו בביקור.
```
- **gonorrhea** | chapters ['ch14'] → sections ['N30-N39'] (85 codes) → 85 cands → **NONE** (high)
- **sensorineural hearing loss, left ear** | chapters ['ch8'] → sections ['H80-H83', 'H90-H94'] (185 codes) → H90(18) → 18 cands → **H90.42** (high)
  - gold A54.9 [matched dx: gonorrhea]: Ch.1 Certain infectious and parasitic diseases (A00-B99) > Infections with a predominantly sexual mode of transmission (A50-A64) > A54 Gonococcal infection > A54.9 Gonococcal infection, unspecified
  - gold H91.92 [matched dx: sensorineural hearing loss, left ear]: Ch.8 Diseases of the ear and mastoid process (H60-H95) > Other disorders of ear (H90-H94) > H91 Other and unspecified hearing loss > H91.9 Unspecified hearing loss > H91.92 Unspecified hearing loss, left ear

### V0052  gold=['D53.9', 'I22.9']  pred=['I21.9', 'E63.9', 'D53.9']
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
- **unspecified nutritional deficiency** | chapters ['ch4', 'ch3'] → sections ['E50-E64', 'D50-D53'] (69 codes) → 69 cands → **E63.9** (high)
- **unspecified nutritional anemia** | chapters ['ch3', 'ch4'] → sections ['D50-D53', 'E40-E46'] (27 codes) → 27 cands → **D53.9** (high)
  - gold D53.9 [matched dx: unspecified nutritional anemia]: Ch.3 Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism (D50-D89) > Nutritional anemias (D50-D53) > D53 Other nutritional anemias > D53.9 Nutritional anemia, unspecified
  - gold I22.9 [matched dx: acute myocardial infarction]: Ch.9 Diseases of the circulatory system (I00-I99) > Ischemic heart diseases (I20-I25) > I22 Subsequent ST elevation (STEMI) and non-ST elevation (NSTEMI) myocardial infarction > I22.9 Subsequent ST elevation (STEMI) myocardial infarction of unspecified site

### V0057  gold=['H11.002']  pred=[]
```
ביקור מרפאתי. בן 27.
מתאר/ת כי תחושת גוף זר והפרעה קוסמטית בעין שמאל.
על פי המסמכים: פטריגיום נזלי נראה בבדיקה.
הערכה קלינית ראשונית: פטריגיום בעין שמאל.
הותאם מעקב לפי חומרת הממצאים, ונמסרו סימני אזהרה להערכה חוזרת.
```
- **conjunctival pterygium of the left eye** | chapters ['ch7'] → sections ['H10-H11'] (167 codes) → H10(72) → 72 cands → **NONE** (high)
  - gold H11.002 [matched dx: conjunctival pterygium of the left eye]: Ch.7 Diseases of the eye and adnexa (H00-H59) > Disorders of conjunctiva (H10-H11) > H11 Other disorders of conjunctiva > H11.0 Pterygium of eye > H11.00 Unspecified pterygium of eye > H11.002 Unspecified pterygium of left eye

### V0060  gold=['K56.609']  pred=['K59.1']
```
ביקור מרפאתי. בן 30.
מגיע/ה לבדיקה עקב הקאות חוזרות, נפיחות ואי מעבר גזים.
על פי המסמכים: צילום בטן עם לולאות מורחבות.
סוכם על תוכנית טיפול ומעקב בהתאם לבעיות שנדונו בביקור.
```
- **chronic diarrhea** | chapters ['ch11', 'ch18'] → sections ['K50-K52', 'K55-K64', 'R10-R19'] (347 codes) → K59/R14/R19(44) → 44 cands → **K59.1** (high)
  - gold K56.609 [matched dx: NONE]: Ch.11 Diseases of the digestive system (K00-K95) > Other diseases of intestines (K55-K64) > K56 Paralytic ileus and intestinal obstruction without hernia > K56.6 Other and unspecified intestinal obstruction > K56.60 Unspecified intestinal obstruction > K56.609 Unspecified intestinal obstruction, unspecified as to partial versus complete obstruction

### V0069  gold=['F45.1']  pred=['F45.42']
```
ביקור מרפאתי. בת 63.
תועד גם: מצוקה ותפקוד ירוד סביב התסמינים.
מהשיחה ומהתיק: עיסוק מוגבר בתלונות גופניות למרות בירור נרחב.
הערכה קלינית ראשונית: הפרעת תסמינים סומטיים.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **somatic symptom disorder** | chapters ['ch5'] → sections ['F40-F48'] (71 codes) → 71 cands → **F45.42** (high)
  - gold F45.1 [matched dx: somatic symptom disorder]: Ch.5 Mental, Behavioral and Neurodevelopmental disorders (F01-F99) > Anxiety, dissociative, stress-related, somatoform and other nonpsychotic mental disorders (F40-F48) > F45 Somatoform disorders > F45.1 Undifferentiated somatoform disorder

### V0072  gold=['M34.9']  pred=['M34.0']
```
ביקור מרפאתי. בת 39.
ממצא תומך: ממצאים אופייניים בסקלרודקטיליה.
מהשיחה ומהתיק: התקשות עור אצבעות עם ריינו וצרבת.
לא הועלתה תלונה חריפה נוספת מעבר לנושאים שנדונו.
נידונו אפשרויות טיפול והמשך בירור בהתאם לתמונה הקלינית.
```
- **scleroderma** | chapters ['ch13'] → sections ['M30-M36'] (84 codes) → 84 cands → **M34.0** (high)
  - gold M34.9 [matched dx: scleroderma]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Systemic connective tissue disorders (M30-M36) > M34 Systemic sclerosis [scleroderma] > M34.9 Systemic sclerosis, unspecified

### V0080  gold=['H40.1122', 'M33.20']  pred=['G60.3', 'R26.2', 'G72.0']
```
ביקור מרפאתי. בן 31.
בימים האחרונים דווח כי ירידה מתמשכת בסיבי עצב הראייה משמאל.
תועד גם: OCT ושדה ראייה מתאימים לשלב בינוני.
בנוסף, נדונה בעיה נפרדת: חולשה שרירית פרוקסימלית וקושי לקום מכיסא.
לגבי הבעיה הנוספת נמצאו: CK גבוה מאוד.
סוכם על תוכנית טיפול ומעקב בהתאם לבעיות שנדונו בביקור.
```
- **progressive peripheral neuropathy of the left side** | chapters ['ch6', 'ch7'] → sections ['G60-G65'] (24 codes) → 24 cands → **G60.3** (high)
- **proximal muscle weakness with difficulty standing from sitting** | chapters ['ch13', 'ch18'] → sections ['M60-M63', 'R25-R29', 'R70-R79'] (537 codes) → R26/R74(10) → 10 cands → **R26.2** (high)
- **severe elevated creatine kinase** | chapters ['ch14', 'ch6', 'ch18'] → sections ['G70-G73', 'R70-R79'] (93 codes) → 93 cands → **G72.0** (high)
  - gold H40.1122 [matched dx: NONE]: Ch.7 Diseases of the eye and adnexa (H00-H59) > Glaucoma (H40-H42) > H40 Glaucoma > H40.1 Open-angle glaucoma > H40.11 Primary open-angle glaucoma > H40.112 Primary open-angle glaucoma, left eye > H40.1122 Primary open-angle glaucoma, left eye, moderate stage
  - gold M33.20 [matched dx: proximal muscle weakness with difficulty standing from sitting]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Systemic connective tissue disorders (M30-M36) > M33 Dermatopolymyositis > M33.2 Polymyositis > M33.20 Polymyositis, organ involvement unspecified

### V0082  gold=['L50.9', 'M10.9']  pred=['M10.9', 'R52']
```
ביקור מרפאתי. בן 84.
סיבת הפנייה: תפרחת מגרדת שנודדת ממקום למקום.
בדיקות וממצאים: ללא טריגר ברור.
בסקירת מצב בריאותי נוסף עלה כי התקף כאב ונפיחות במפרק בוהן שהחל בלילה.
לגבי הבעיה הנוספת נמצאו: גבישי אורט בנוזל מפרקי.
נרשם גם: גאוט לא מסווג.
נקבעו בדיקות והנחיות טיפול מותאמות לממצאים שעלו בשיחה ובבדיקה.
```
- **gout, unspecified** | chapters ['ch13'] → sections ['M05-M14'] (1185 codes) → M10(121) → M10.9(1) → 1 cands → **M10.9** (high)
- **pain and swelling in the hip joint** | chapters ['ch13', 'ch18'] → sections ['M05-M14', 'M70-M79', 'R50-R69'] (1611 codes) → M10/R52/R60(125) → M10.9/R52/R60.0(3) → 3 cands → **R52** (high)
- **uric acid crystals in joint fluid** | chapters ['ch13', 'ch18'] → sections ['M05-M14'] (1185 codes) → M10(121) → M10.9(1) → 1 cands → **M10.9** (high)
  - gold L50.9 [matched dx: NONE]: Ch.12 Diseases of the skin and subcutaneous tissue (L00-L99) > Urticaria and erythema (L49-L54) > L50 Urticaria > L50.9 Urticaria, unspecified
  - gold M10.9 [matched dx: gout, unspecified]: Ch.13 Diseases of the musculoskeletal system and connective tissue (M00-M99) > Inflammatory polyarthropathies (M05-M14) > M10 Gout > M10.9 Gout, unspecified
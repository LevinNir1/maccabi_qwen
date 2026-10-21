# Example flow: every prompt and answer for one visit

A made-up demo visit (`docs/demo_visit.json`, not from the provided data) run through the pipeline with the default model `qwen3:4b-instruct-2507-q8_0`: **8 model calls, 24 s** on an Apple M1 Max GPU. Regenerate the output with `curl -s -X POST localhost:8000/predict?debug=true -H 'Content-Type: application/json' -d @docs/demo_visit.json`.

```text
ביקור מרפאתי. בת 52.
סיבת הפנייה: צמא מוגבר ומתן שתן תכוף בחודשים האחרונים.
בבדיקות הדם: HbA1c 8.1% וסוכר בצום 168.
בנוסף, נדונה בעיה נפרדת: כאב בברך ימין בעלייה במדרגות.
הממצא המחזק: צילום מראה היצרות של המרווח המפרקי בברך ימין.
סוכם על התחלת טיפול והמשך מעקב.
```

(Diabetes symptoms with HbA1c 8.1%, plus right knee pain on stairs with joint-space narrowing on X-ray.)

## The flow at a glance

| Call | Diagnosis                        | Step              | Options shown     | Answer      | Meaning                                                                                                     |
| ---- | -------------------------------- | ----------------- | ----------------- | ----------- | ----------------------------------------------------------------------------------------------------------- |
| 1    | —                                | Extract diagnoses | the note          | 2 diagnoses | type 2 diabetes mellitus; right knee joint space narrowing                                                  |
| 2    | type 2 diabetes mellitus         | Chapter           | 22                | `[4]`       | Endocrine, nutritional and metabolic diseases                                                               |
| 3    | type 2 diabetes mellitus         | Section           | 10                | `[2]`       | Diabetes mellitus [chapter: Endocrine, nutritional and metabolic diseases]                                  |
| 4    | type 2 diabetes mellitus         | Category          | 5                 | `[4]`       | E11 Type 2 diabetes mellitus                                                                                |
| 5    | type 2 diabetes mellitus         | Final code        | 87 codes + "none" | `86`, high  | **E11.9** Type 2 diabetes mellitus without complications                                                    |
| 6    | right knee joint space narrowing | Chapter           | 22                | `[13, 4]`   | Diseases of the musculoskeletal system and connective tissue; Endocrine, nutritional and metabolic diseases |
| 7    | right knee joint space narrowing | Section           | 30                | `[4]`       | Osteoarthritis [chapter: Diseases of the musculoskeletal system and connective tissue]                      |
| 8    | right knee joint space narrowing | Final code        | 98 codes + "none" | `25`, high  | **M17.11** Unilateral primary osteoarthritis, right knee                                                    |

- **type 2 diabetes mellitus**: the chosen sections hold 432 billable codes (more than MAX_CODES = 100), so the path is section → category → code; 87 candidates reach the final step.
- **right knee joint space narrowing**: the chosen sections hold 98 billable codes (not more than MAX_CODES = 100), so the path is section → code directly; 98 candidates reach the final step.

Between calls, Python maps each answer number back to its ICD node, counts the billable codes under the chosen nodes to decide whether a category step is needed, builds the next numbered option list, checks each evidence quote against the note, and finally validates and deduplicates the codes.

## Final output

```json
{
 "visit_id": "DEMO1",
 "predictions": [
  {
   "code": "E11.9",
   "description": "Type 2 diabetes mellitus without complications",
   "score": 0.9,
   "evidence": "בבדיקות הדם: HbA1c 8.1% וסוכר בצום 168",
   "evidence_verbatim": true
  },
  {
   "code": "M17.11",
   "description": "Unilateral primary osteoarthritis, right knee",
   "score": 0.9,
   "evidence": "הממצא המחזק: צילום מראה היצרות של המרווח המפרקי בברך ימין",
   "evidence_verbatim": true
  }
 ]
}
```

## The prompts (exact text, from `src/prompts.py`)

Every call sends a system message (instructions) and a user message (the visit and the options). The answer is constrained by a JSON schema, so the model can only return valid option numbers.

**1. Extract diagnoses — system message**

```text
You are an expert clinical coder. You read Hebrew outpatient visit notes and identify the diagnoses that should be coded with ICD-10-CM.

Rules:
- Each distinct clinical problem addressed in the visit usually corresponds to one diagnosis.
- Infer the most specific diagnosis that the documented symptoms, findings and test results establish, even when it is not named explicitly (e.g. potassium 6.2 -> hyperkalemia; EMG showing neuropathy -> peripheral neuropathy).
- If the visit is for a preventive service (vaccination, screening, routine check), give that encounter reason as the diagnosis.
- Use a symptom as the diagnosis only when no underlying diagnosis is established.
- Do not include negated or ruled-out conditions, or generic administrative sentences.
- diagnosis: a precise English clinical term that keeps the documented details (type, severity, acuity, site, laterality, and for injuries the encounter: initial/subsequent).
- evidence: copy the supporting text EXACTLY, verbatim, from the Hebrew note (one sentence or phrase, not translated).

Respond only with JSON: {"diagnoses": [{"diagnosis": "...", "evidence": "..."}]}
```

**2. Choose chapters / sections / categories — system message** (`{what}` and `{k}` are filled in per step)

```text
You are an expert ICD-10-CM coder. Given a diagnosis from a clinical note, choose the ICD-10-CM {what} that contain the correct code for it.
Select up to {k} options, most likely first. Add more only if the correct code could plausibly be there.
Answer with the option numbers. Respond only with JSON: {"selected": [<number>, ...]}
```

**3. Choose the final code — system message**

```text
You are an expert ICD-10-CM coder. Choose the single ICD-10-CM code that best matches the diagnosis as documented in the note.
- Prefer the most specific code that the note supports (type, site, laterality, severity, encounter).
- Use an "unspecified" code when the detail is not documented.
- Choose 0 if no code in the list fits the diagnosis.
confidence: high = the code clearly matches the documentation; medium = a reasonable choice but details are uncertain; low = a weak match.
Respond only with JSON: {"choice": <number>, "confidence": "high|medium|low"}
```

**User message for steps 2–3** (the diagnosis being coded, plus the numbered options)

```text
Patient: age {age}, sex {sex}. Clinic: {physician_specialty}.
Note:
{note_text}

Diagnosis to code: {diagnosis}
Evidence: {evidence}

Options:
{options}
```

## Every call in full

### Call 1 — extract diagnoses

User message:

```text
Patient: age 52, sex F. Clinic: Family Medicine. Visit type: new, in_person, community_clinic.

Note:
ביקור מרפאתי. בת 52.
סיבת הפנייה: צמא מוגבר ומתן שתן תכוף בחודשים האחרונים.
בבדיקות הדם: HbA1c 8.1% וסוכר בצום 168.
בנוסף, נדונה בעיה נפרדת: כאב בברך ימין בעלייה במדרגות.
הממצא המחזק: צילום מראה היצרות של המרווח המפרקי בברך ימין.
סוכם על התחלת טיפול והמשך מעקב.
```

Model answer:

```json
{"diagnoses": [{"diagnosis": "type 2 diabetes mellitus", "evidence": "בבדיקות הדם: HbA1c 8.1% וסוכר בצום 168"}, {"diagnosis": "right knee joint space narrowing", "evidence": "הממצא המחזק: צילום מראה היצרות של המרווח המפרקי בברך ימין"}]}
```

### Call 2 — type 2 diabetes mellitus: choose chapters

User message (patient line and note as above, then):

```text
Diagnosis to code: type 2 diabetes mellitus
Evidence: בבדיקות הדם: HbA1c 8.1% וסוכר בצום 168

Options:
1. Certain infectious and parasitic diseases. Sections: Intestinal infectious diseases; Tuberculosis; Certain zoonotic bacterial diseases; Other bacterial diseases; Infections with a predominantly sexual mode of transmission; Other spirochetal diseases; Other diseases caused by chlamydiae; Rickettsioses; Viral and prion infections of the central nervous system; Arthropod-borne viral fevers and viral hemorrhagic fevers; Viral infections characterized by skin and mucous membrane lesions; Other human herpesviruses; Viral hepatitis; Human immunodeficiency virus [HIV] disease; Other viral diseases; Mycoses; Protozoal diseases; Helminthiases; Pediculosis, acariasis and other infestations; Sequelae of infectious and parasitic diseases; Bacterial and viral infectious agents; Other infectious diseases
2. Neoplasms. Sections: Malignant neoplasms of lip, oral cavity and pharynx; Malignant neoplasms of digestive organs; Malignant neoplasms of respiratory and intrathoracic organs; Malignant neoplasms of bone and articular cartilage; Melanoma and other malignant neoplasms of skin; Malignant neoplasms of mesothelial and soft tissue; Malignant neoplasms of breast; Malignant neoplasms of female genital organs; Malignant neoplasms of male genital organs; Malignant neoplasms of urinary tract; Malignant neoplasms of eye, brain and other parts of central nervous system; Malignant neoplasms of thyroid and other endocrine glands; Malignant neuroendocrine tumors; Secondary neuroendocrine tumors; Malignant neoplasms of ill-defined, other secondary and unspecified sites; Malignant neoplasms of lymphoid, hematopoietic and related tissue; In situ neoplasms; Benign neoplasms, except benign neuroendocrine tumors; Benign neuroendocrine tumors; Neoplasms of uncertain behavior, polycythemia vera and myelodysplastic syndromes; Neoplasms of unspecified behavior
3. Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism. Sections: Nutritional anemias; Hemolytic anemias; Aplastic and other anemias and other bone marrow failure syndromes; Coagulation defects, purpura and other hemorrhagic conditions; Other disorders of blood and blood-forming organs; Intraoperative and postprocedural complications of the spleen; Certain disorders involving the immune mechanism
4. Endocrine, nutritional and metabolic diseases. Sections: Disorders of thyroid gland; Diabetes mellitus; Other disorders of glucose regulation and pancreatic internal secretion; Disorders of other endocrine glands; Intraoperative complications of endocrine system; Malnutrition; Other nutritional deficiencies; Overweight, obesity and other hyperalimentation; Metabolic disorders; Postprocedural endocrine and metabolic complications and disorders, not elsewhere classified
5. Mental, Behavioral and Neurodevelopmental disorders. Sections: Mental disorders due to known physiological conditions; Mental and behavioral disorders due to psychoactive substance use; Schizophrenia, schizotypal, delusional, and other non-mood psychotic disorders; Mood [affective] disorders; Anxiety, dissociative, stress-related, somatoform and other nonpsychotic mental disorders; Behavioral syndromes associated with physiological disturbances and physical factors; Disorders of adult personality and behavior; Intellectual Disabilities; Pervasive and specific developmental disorders; Behavioral and emotional disorders with onset usually occurring in childhood and adolescence; Unspecified mental disorder
6. Diseases of the nervous system. Sections: Inflammatory diseases of the central nervous system; Systemic atrophies primarily affecting the central nervous system; Extrapyramidal and movement disorders; Other degenerative diseases of the nervous system; Demyelinating diseases of the central nervous system; Episodic and paroxysmal disorders; Nerve, nerve root and plexus disorders; Polyneuropathies and other disorders of the peripheral nervous system; Diseases of myoneural junction and muscle; Cerebral palsy and other paralytic syndromes; Other disorders of the nervous system
7. Diseases of the eye and adnexa. Sections: Disorders of eyelid, lacrimal system and orbit; Disorders of conjunctiva; Disorders of sclera, cornea, iris and ciliary body; Disorders of lens; Disorders of choroid and retina; Glaucoma; Disorders of vitreous body and globe; Disorders of optic nerve and visual pathways; Disorders of ocular muscles, binocular movement, accommodation and refraction; Visual disturbances and blindness; Other disorders of eye and adnexa; Intraoperative and postprocedural complications and disorders of eye and adnexa, not elsewhere classified
8. Diseases of the ear and mastoid process. Sections: Diseases of external ear; Diseases of middle ear and mastoid; Diseases of inner ear; Other disorders of ear; Intraoperative and postprocedural complications and disorders of ear and mastoid process, not elsewhere classified
9. Diseases of the circulatory system. Sections: Acute rheumatic fever; Chronic rheumatic heart diseases; Hypertensive diseases; Ischemic heart diseases; Pulmonary heart disease and diseases of pulmonary circulation; Other forms of heart disease; Cerebrovascular diseases; Diseases of arteries, arterioles and capillaries; Diseases of veins, lymphatic vessels and lymph nodes, not elsewhere classified; Other and unspecified disorders of the circulatory system
10. Diseases of the respiratory system. Sections: Acute upper respiratory infections; Influenza and pneumonia; Other acute lower respiratory infections; Other diseases of upper respiratory tract; Chronic lower respiratory diseases; Lung diseases due to external agents; Other respiratory diseases principally affecting the interstitium; Suppurative and necrotic conditions of the lower respiratory tract; Other diseases of the pleura; Intraoperative and postprocedural complications and disorders of respiratory system, not elsewhere classified; Other diseases of the respiratory system
11. Diseases of the digestive system. Sections: Diseases of oral cavity and salivary glands; Diseases of esophagus, stomach and duodenum; Diseases of appendix; Hernia; Noninfective enteritis and colitis; Other diseases of intestines; Diseases of peritoneum, retroperitoneum and pelvis; Diseases of liver; Disorders of gallbladder, biliary tract and pancreas; Other diseases of the digestive system
12. Diseases of the skin and subcutaneous tissue. Sections: Infections of the skin and subcutaneous tissue; Bullous disorders; Dermatitis and eczema; Papulosquamous disorders; Urticaria and erythema; Radiation-related disorders of the skin and subcutaneous tissue; Disorders of skin appendages; Intraoperative and postprocedural complications of skin and subcutaneous tissue; Other disorders of the skin and subcutaneous tissue
13. Diseases of the musculoskeletal system and connective tissue. Sections: Infectious arthropathies; Autoinflammatory syndromes; Inflammatory polyarthropathies; Osteoarthritis; Other joint disorders; Dentofacial anomalies [including malocclusion] and other disorders of jaw; Systemic connective tissue disorders; Deforming dorsopathies; Spondylopathies; Other dorsopathies; Disorders of muscles; Disorders of synovium and tendon; Other soft tissue disorders; Disorders of bone density and structure; Other osteopathies; Chondropathies; Other disorders of the musculoskeletal system and connective tissue; Intraoperative and postprocedural complications and disorders of musculoskeletal system, not elsewhere classified; Periprosthetic fracture around internal prosthetic joint; Biomechanical lesions, not elsewhere classified
14. Diseases of the genitourinary system. Sections: Glomerular diseases; Renal tubulo-interstitial diseases; Acute kidney failure and chronic kidney disease; Urolithiasis; Other disorders of kidney and ureter; Other diseases of the urinary system; Diseases of male genital organs; Disorders of breast; Inflammatory diseases of female pelvic organs; Noninflammatory disorders of female genital tract; Intraoperative and postprocedural complications and disorders of genitourinary system, not elsewhere classified
15. Pregnancy, childbirth and the puerperium. Sections: Pregnancy with abortive outcome; Supervision of high risk pregnancy; Edema, proteinuria and hypertensive disorders in pregnancy, childbirth and the puerperium; Other maternal disorders predominantly related to pregnancy; Maternal care related to the fetus and amniotic cavity and possible delivery problems; Complications of labor and delivery; Encounter for delivery; Complications predominantly related to the puerperium; Other obstetric conditions, not elsewhere classified
16. Certain conditions originating in the perinatal period. Sections: Newborn affected by maternal factors and by complications of pregnancy, labor, and delivery; Disorders of newborn related to length of gestation and fetal growth; Abnormal findings on neonatal screening; Birth trauma; Respiratory and cardiovascular disorders specific to the perinatal period; Infections specific to the perinatal period; Hemorrhagic and hematological disorders of newborn; Transitory endocrine and metabolic disorders specific to newborn; Digestive system disorders of newborn; Conditions involving the integument and temperature regulation of newborn; Other problems with newborn; Other disorders originating in the perinatal period
17. Congenital malformations, deformations, chromosomal abnormalities, and genetic disorders. Sections: Congenital malformations of the nervous system; Congenital malformations of eye, ear, face and neck; Congenital malformations of the circulatory system; Congenital malformations of the respiratory system; Cleft lip and cleft palate; Other congenital malformations of the digestive system; Congenital malformations of genital organs; Congenital malformations of the urinary system; Congenital malformations and deformations of the musculoskeletal system; Other congenital malformations; Chromosomal abnormalities, not elsewhere classified; Genetic disorders, not elsewhere classified
18. Symptoms, signs and abnormal clinical and laboratory findings, not elsewhere classified. Sections: Symptoms and signs involving the circulatory and respiratory systems; Symptoms and signs involving the digestive system and abdomen; Symptoms and signs involving the skin and subcutaneous tissue; Symptoms and signs involving the nervous and musculoskeletal systems; Symptoms and signs involving the genitourinary system; Symptoms and signs involving cognition, perception, emotional state and behavior; Symptoms and signs involving speech and voice; General symptoms and signs; Abnormal findings on examination of blood, without diagnosis; Abnormal findings on examination of urine, without diagnosis; Abnormal findings on examination of other body fluids, substances and tissues, without diagnosis; Abnormal findings on diagnostic imaging and in function studies, without diagnosis; Abnormal tumor markers; Ill-defined and unknown cause of mortality
19. Injury, poisoning and certain other consequences of external causes. Sections: Injuries to the head; Injuries to the neck; Injuries to the thorax; Injuries to the abdomen, lower back, lumbar spine, pelvis and external genitals; Injuries to the shoulder and upper arm; Injuries to the elbow and forearm; Injuries to the wrist, hand and fingers; Injuries to the hip and thigh; Injuries to the knee and lower leg; Injuries to the ankle and foot; Injuries involving multiple body regions; Injury of unspecified body region; Effects of foreign body entering through natural orifice; Burns and corrosions of external body surface, specified by site; Burns and corrosions confined to eye and internal organs; Burns and corrosions of multiple and unspecified body regions; Frostbite; Poisoning by, adverse effects of and underdosing of drugs, medicaments and biological substances; Toxic effects of substances chiefly nonmedicinal as to source; Other and unspecified effects of external causes; Certain early complications of trauma; Complications of surgical and medical care, not elsewhere classified
20. External causes of morbidity. Sections: Pedestrian injured in transport accident; Pedal cycle rider injured in transport accident; Motorcycle rider injured in transport accident; Occupant of three-wheeled motor vehicle injured in transport accident; Car occupant injured in transport accident; Occupant of pick-up truck or van injured in transport accident; Occupant of heavy transport vehicle injured in transport accident; Bus occupant injured in transport accident; Other land transport accidents; Water transport accidents; Air and space transport accidents; Other and unspecified transport accidents; Slipping, tripping, stumbling and falls; Exposure to inanimate mechanical forces; Exposure to animate mechanical forces; Accidental non-transport drowning and submersion; Exposure to electric current, radiation and extreme ambient air temperature and pressure; Exposure to smoke, fire and flames; Contact with heat and hot substances; Exposure to forces of nature; Overexertion and strenuous or repetitive movements; Accidental exposure to other specified factors; Intentional self-harm; Assault; Event of undetermined intent; Legal intervention, operations of war, military operations, and terrorism; Misadventures to patients during surgical and medical care; Medical devices associated with adverse incidents in diagnostic and therapeutic use; Surgical and other medical procedures as the cause of abnormal reaction of the patient, or of later complication, without mention of misadventure at the time of the procedure; Supplementary factors related to causes of morbidity classified elsewhere
21. Factors influencing health status and contact with health services. Sections: Persons encountering health services for examinations; Genetic carrier and genetic susceptibility to disease; Resistance to antimicrobial drugs; Estrogen, and other hormones and factors receptor status; Retained foreign body fragments; Hormone sensitivity malignancy status; Persons with potential health hazards related to communicable diseases; Persons encountering health services in circumstances related to reproduction; Encounters for other specific health care; Persons with potential health hazards related to socioeconomic and psychosocial circumstances; Do not resuscitate status; Blood type; Body mass index [BMI]; Persons encountering health services in other circumstances; Persons with potential health hazards related to family and personal history and certain conditions influencing health status
22. Codes for special purposes. Sections: Provisional assignment of new diseases of uncertain etiology or emergency use
```

Model answer:

```json
{"selected": [4]}
```

### Call 3 — type 2 diabetes mellitus: choose sections

User message (patient line and note as above, then):

```text
Diagnosis to code: type 2 diabetes mellitus
Evidence: בבדיקות הדם: HbA1c 8.1% וסוכר בצום 168

Options:
1. Disorders of thyroid gland [chapter: Endocrine, nutritional and metabolic diseases]. Includes: Congenital iodine-deficiency syndrome; Iodine-deficiency related thyroid disorders and allied conditions; Subclinical iodine-deficiency hypothyroidism; Other hypothyroidism; Other nontoxic goiter; Thyrotoxicosis [hyperthyroidism]; Thyroiditis; Other disorders of thyroid
2. Diabetes mellitus [chapter: Endocrine, nutritional and metabolic diseases]. Includes: Diabetes mellitus due to underlying condition; Drug or chemical induced diabetes mellitus; Type 1 diabetes mellitus; Type 2 diabetes mellitus; Other specified diabetes mellitus
3. Other disorders of glucose regulation and pancreatic internal secretion [chapter: Endocrine, nutritional and metabolic diseases]. Includes: Nondiabetic hypoglycemic coma; Other disorders of pancreatic internal secretion
4. Disorders of other endocrine glands [chapter: Endocrine, nutritional and metabolic diseases]. Includes: Hypoparathyroidism; Hyperparathyroidism and other disorders of parathyroid gland; Hyperfunction of pituitary gland; Hypofunction and other disorders of the pituitary gland; Cushing's syndrome; Adrenogenital disorders; Hyperaldosteronism; Other disorders of adrenal gland; Ovarian dysfunction; Testicular dysfunction; Disorders of puberty, not elsewhere classified; Polyglandular dysfunction; Diseases of thymus; Other endocrine disorders; Disorders of endocrine glands in diseases classified elsewhere
5. Intraoperative complications of endocrine system [chapter: Endocrine, nutritional and metabolic diseases]. Includes: Intraoperative complications of endocrine system
6. Malnutrition [chapter: Endocrine, nutritional and metabolic diseases]. Includes: Kwashiorkor; Nutritional marasmus; Marasmic kwashiorkor; Unspecified severe protein-calorie malnutrition; Protein-calorie malnutrition of moderate and mild degree; Retarded development following protein-calorie malnutrition; Unspecified protein-calorie malnutrition
7. Other nutritional deficiencies [chapter: Endocrine, nutritional and metabolic diseases]. Includes: Vitamin A deficiency; Thiamine deficiency; Niacin deficiency [pellagra]; Deficiency of other B group vitamins; Ascorbic acid deficiency; Vitamin D deficiency; Other vitamin deficiencies; Dietary calcium deficiency; Dietary selenium deficiency; Dietary zinc deficiency; Deficiency of other nutrient elements; Other nutritional deficiencies; Sequelae of malnutrition and other nutritional deficiencies
8. Overweight, obesity and other hyperalimentation [chapter: Endocrine, nutritional and metabolic diseases]. Includes: Localized adiposity; Overweight and obesity; Other hyperalimentation; Sequelae of hyperalimentation
9. Metabolic disorders [chapter: Endocrine, nutritional and metabolic diseases]. Includes: Disorders of aromatic amino-acid metabolism; Disorders of branched-chain amino-acid metabolism and fatty-acid metabolism; Other disorders of amino-acid metabolism; Lactose intolerance; Other disorders of carbohydrate metabolism; Disorders of sphingolipid metabolism and other lipid storage disorders; Disorders of glycosaminoglycan metabolism; Disorders of glycoprotein metabolism; Disorders of lipoprotein metabolism and other lipidemias; Disorders of purine and pyrimidine metabolism; Disorders of porphyrin and bilirubin metabolism; Disorders of mineral metabolism; Cystic fibrosis; Amyloidosis; Volume depletion; Other disorders of fluid, electrolyte and acid-base balance; Other and unspecified metabolic disorders
10. Postprocedural endocrine and metabolic complications and disorders, not elsewhere classified [chapter: Endocrine, nutritional and metabolic diseases]. Includes: Postprocedural endocrine and metabolic complications and disorders, not elsewhere classified
```

Model answer:

```json
{"selected": [2]}
```

### Call 4 — type 2 diabetes mellitus: choose groups

User message (patient line and note as above, then):

```text
Diagnosis to code: type 2 diabetes mellitus
Evidence: בבדיקות הדם: HbA1c 8.1% וסוכר בצום 168

Options:
1. E08 Diabetes mellitus due to underlying condition [within: Diabetes mellitus (E08-E13)]
2. E09 Drug or chemical induced diabetes mellitus [within: Diabetes mellitus (E08-E13)]
3. E10 Type 1 diabetes mellitus [within: Diabetes mellitus (E08-E13)]
4. E11 Type 2 diabetes mellitus [within: Diabetes mellitus (E08-E13)]
5. E13 Other specified diabetes mellitus [within: Diabetes mellitus (E08-E13)]
```

Model answer:

```json
{"selected": [4]}
```

### Call 5 — type 2 diabetes mellitus: choose final code

User message (patient line and note as above, then):

```text
Diagnosis to code: type 2 diabetes mellitus
Evidence: בבדיקות הדם: HbA1c 8.1% וסוכר בצום 168

Options:
0. none of these codes fits
1. E11.00 Type 2 diabetes mellitus with hyperosmolarity without nonketotic hyperglycemic-hyperosmolar coma (NKHHC)
2. E11.01 Type 2 diabetes mellitus with hyperosmolarity with coma
3. E11.10 Type 2 diabetes mellitus with ketoacidosis without coma
4. E11.11 Type 2 diabetes mellitus with ketoacidosis with coma
5. E11.21 Type 2 diabetes mellitus with diabetic nephropathy
… (80 more options)
86. E11.9 Type 2 diabetes mellitus without complications
… (1 more option)
```

Model answer:

```json
{"choice": 86, "confidence": "high"}
```

### Call 6 — right knee joint space narrowing: choose chapters

User message (patient line and note as above, then):

```text
Diagnosis to code: right knee joint space narrowing
Evidence: הממצא המחזק: צילום מראה היצרות של המרווח המפרקי בברך ימין

Options:
1. Certain infectious and parasitic diseases. Sections: Intestinal infectious diseases; Tuberculosis; Certain zoonotic bacterial diseases; Other bacterial diseases; Infections with a predominantly sexual mode of transmission; Other spirochetal diseases; Other diseases caused by chlamydiae; Rickettsioses; Viral and prion infections of the central nervous system; Arthropod-borne viral fevers and viral hemorrhagic fevers; Viral infections characterized by skin and mucous membrane lesions; Other human herpesviruses; Viral hepatitis; Human immunodeficiency virus [HIV] disease; Other viral diseases; Mycoses; Protozoal diseases; Helminthiases; Pediculosis, acariasis and other infestations; Sequelae of infectious and parasitic diseases; Bacterial and viral infectious agents; Other infectious diseases
2. Neoplasms. Sections: Malignant neoplasms of lip, oral cavity and pharynx; Malignant neoplasms of digestive organs; Malignant neoplasms of respiratory and intrathoracic organs; Malignant neoplasms of bone and articular cartilage; Melanoma and other malignant neoplasms of skin; Malignant neoplasms of mesothelial and soft tissue; Malignant neoplasms of breast; Malignant neoplasms of female genital organs; Malignant neoplasms of male genital organs; Malignant neoplasms of urinary tract; Malignant neoplasms of eye, brain and other parts of central nervous system; Malignant neoplasms of thyroid and other endocrine glands; Malignant neuroendocrine tumors; Secondary neuroendocrine tumors; Malignant neoplasms of ill-defined, other secondary and unspecified sites; Malignant neoplasms of lymphoid, hematopoietic and related tissue; In situ neoplasms; Benign neoplasms, except benign neuroendocrine tumors; Benign neuroendocrine tumors; Neoplasms of uncertain behavior, polycythemia vera and myelodysplastic syndromes; Neoplasms of unspecified behavior
3. Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism. Sections: Nutritional anemias; Hemolytic anemias; Aplastic and other anemias and other bone marrow failure syndromes; Coagulation defects, purpura and other hemorrhagic conditions; Other disorders of blood and blood-forming organs; Intraoperative and postprocedural complications of the spleen; Certain disorders involving the immune mechanism
4. Endocrine, nutritional and metabolic diseases. Sections: Disorders of thyroid gland; Diabetes mellitus; Other disorders of glucose regulation and pancreatic internal secretion; Disorders of other endocrine glands; Intraoperative complications of endocrine system; Malnutrition; Other nutritional deficiencies; Overweight, obesity and other hyperalimentation; Metabolic disorders; Postprocedural endocrine and metabolic complications and disorders, not elsewhere classified
5. Mental, Behavioral and Neurodevelopmental disorders. Sections: Mental disorders due to known physiological conditions; Mental and behavioral disorders due to psychoactive substance use; Schizophrenia, schizotypal, delusional, and other non-mood psychotic disorders; Mood [affective] disorders; Anxiety, dissociative, stress-related, somatoform and other nonpsychotic mental disorders; Behavioral syndromes associated with physiological disturbances and physical factors; Disorders of adult personality and behavior; Intellectual Disabilities; Pervasive and specific developmental disorders; Behavioral and emotional disorders with onset usually occurring in childhood and adolescence; Unspecified mental disorder
6. Diseases of the nervous system. Sections: Inflammatory diseases of the central nervous system; Systemic atrophies primarily affecting the central nervous system; Extrapyramidal and movement disorders; Other degenerative diseases of the nervous system; Demyelinating diseases of the central nervous system; Episodic and paroxysmal disorders; Nerve, nerve root and plexus disorders; Polyneuropathies and other disorders of the peripheral nervous system; Diseases of myoneural junction and muscle; Cerebral palsy and other paralytic syndromes; Other disorders of the nervous system
7. Diseases of the eye and adnexa. Sections: Disorders of eyelid, lacrimal system and orbit; Disorders of conjunctiva; Disorders of sclera, cornea, iris and ciliary body; Disorders of lens; Disorders of choroid and retina; Glaucoma; Disorders of vitreous body and globe; Disorders of optic nerve and visual pathways; Disorders of ocular muscles, binocular movement, accommodation and refraction; Visual disturbances and blindness; Other disorders of eye and adnexa; Intraoperative and postprocedural complications and disorders of eye and adnexa, not elsewhere classified
8. Diseases of the ear and mastoid process. Sections: Diseases of external ear; Diseases of middle ear and mastoid; Diseases of inner ear; Other disorders of ear; Intraoperative and postprocedural complications and disorders of ear and mastoid process, not elsewhere classified
9. Diseases of the circulatory system. Sections: Acute rheumatic fever; Chronic rheumatic heart diseases; Hypertensive diseases; Ischemic heart diseases; Pulmonary heart disease and diseases of pulmonary circulation; Other forms of heart disease; Cerebrovascular diseases; Diseases of arteries, arterioles and capillaries; Diseases of veins, lymphatic vessels and lymph nodes, not elsewhere classified; Other and unspecified disorders of the circulatory system
10. Diseases of the respiratory system. Sections: Acute upper respiratory infections; Influenza and pneumonia; Other acute lower respiratory infections; Other diseases of upper respiratory tract; Chronic lower respiratory diseases; Lung diseases due to external agents; Other respiratory diseases principally affecting the interstitium; Suppurative and necrotic conditions of the lower respiratory tract; Other diseases of the pleura; Intraoperative and postprocedural complications and disorders of respiratory system, not elsewhere classified; Other diseases of the respiratory system
11. Diseases of the digestive system. Sections: Diseases of oral cavity and salivary glands; Diseases of esophagus, stomach and duodenum; Diseases of appendix; Hernia; Noninfective enteritis and colitis; Other diseases of intestines; Diseases of peritoneum, retroperitoneum and pelvis; Diseases of liver; Disorders of gallbladder, biliary tract and pancreas; Other diseases of the digestive system
12. Diseases of the skin and subcutaneous tissue. Sections: Infections of the skin and subcutaneous tissue; Bullous disorders; Dermatitis and eczema; Papulosquamous disorders; Urticaria and erythema; Radiation-related disorders of the skin and subcutaneous tissue; Disorders of skin appendages; Intraoperative and postprocedural complications of skin and subcutaneous tissue; Other disorders of the skin and subcutaneous tissue
13. Diseases of the musculoskeletal system and connective tissue. Sections: Infectious arthropathies; Autoinflammatory syndromes; Inflammatory polyarthropathies; Osteoarthritis; Other joint disorders; Dentofacial anomalies [including malocclusion] and other disorders of jaw; Systemic connective tissue disorders; Deforming dorsopathies; Spondylopathies; Other dorsopathies; Disorders of muscles; Disorders of synovium and tendon; Other soft tissue disorders; Disorders of bone density and structure; Other osteopathies; Chondropathies; Other disorders of the musculoskeletal system and connective tissue; Intraoperative and postprocedural complications and disorders of musculoskeletal system, not elsewhere classified; Periprosthetic fracture around internal prosthetic joint; Biomechanical lesions, not elsewhere classified
14. Diseases of the genitourinary system. Sections: Glomerular diseases; Renal tubulo-interstitial diseases; Acute kidney failure and chronic kidney disease; Urolithiasis; Other disorders of kidney and ureter; Other diseases of the urinary system; Diseases of male genital organs; Disorders of breast; Inflammatory diseases of female pelvic organs; Noninflammatory disorders of female genital tract; Intraoperative and postprocedural complications and disorders of genitourinary system, not elsewhere classified
15. Pregnancy, childbirth and the puerperium. Sections: Pregnancy with abortive outcome; Supervision of high risk pregnancy; Edema, proteinuria and hypertensive disorders in pregnancy, childbirth and the puerperium; Other maternal disorders predominantly related to pregnancy; Maternal care related to the fetus and amniotic cavity and possible delivery problems; Complications of labor and delivery; Encounter for delivery; Complications predominantly related to the puerperium; Other obstetric conditions, not elsewhere classified
16. Certain conditions originating in the perinatal period. Sections: Newborn affected by maternal factors and by complications of pregnancy, labor, and delivery; Disorders of newborn related to length of gestation and fetal growth; Abnormal findings on neonatal screening; Birth trauma; Respiratory and cardiovascular disorders specific to the perinatal period; Infections specific to the perinatal period; Hemorrhagic and hematological disorders of newborn; Transitory endocrine and metabolic disorders specific to newborn; Digestive system disorders of newborn; Conditions involving the integument and temperature regulation of newborn; Other problems with newborn; Other disorders originating in the perinatal period
17. Congenital malformations, deformations, chromosomal abnormalities, and genetic disorders. Sections: Congenital malformations of the nervous system; Congenital malformations of eye, ear, face and neck; Congenital malformations of the circulatory system; Congenital malformations of the respiratory system; Cleft lip and cleft palate; Other congenital malformations of the digestive system; Congenital malformations of genital organs; Congenital malformations of the urinary system; Congenital malformations and deformations of the musculoskeletal system; Other congenital malformations; Chromosomal abnormalities, not elsewhere classified; Genetic disorders, not elsewhere classified
18. Symptoms, signs and abnormal clinical and laboratory findings, not elsewhere classified. Sections: Symptoms and signs involving the circulatory and respiratory systems; Symptoms and signs involving the digestive system and abdomen; Symptoms and signs involving the skin and subcutaneous tissue; Symptoms and signs involving the nervous and musculoskeletal systems; Symptoms and signs involving the genitourinary system; Symptoms and signs involving cognition, perception, emotional state and behavior; Symptoms and signs involving speech and voice; General symptoms and signs; Abnormal findings on examination of blood, without diagnosis; Abnormal findings on examination of urine, without diagnosis; Abnormal findings on examination of other body fluids, substances and tissues, without diagnosis; Abnormal findings on diagnostic imaging and in function studies, without diagnosis; Abnormal tumor markers; Ill-defined and unknown cause of mortality
19. Injury, poisoning and certain other consequences of external causes. Sections: Injuries to the head; Injuries to the neck; Injuries to the thorax; Injuries to the abdomen, lower back, lumbar spine, pelvis and external genitals; Injuries to the shoulder and upper arm; Injuries to the elbow and forearm; Injuries to the wrist, hand and fingers; Injuries to the hip and thigh; Injuries to the knee and lower leg; Injuries to the ankle and foot; Injuries involving multiple body regions; Injury of unspecified body region; Effects of foreign body entering through natural orifice; Burns and corrosions of external body surface, specified by site; Burns and corrosions confined to eye and internal organs; Burns and corrosions of multiple and unspecified body regions; Frostbite; Poisoning by, adverse effects of and underdosing of drugs, medicaments and biological substances; Toxic effects of substances chiefly nonmedicinal as to source; Other and unspecified effects of external causes; Certain early complications of trauma; Complications of surgical and medical care, not elsewhere classified
20. External causes of morbidity. Sections: Pedestrian injured in transport accident; Pedal cycle rider injured in transport accident; Motorcycle rider injured in transport accident; Occupant of three-wheeled motor vehicle injured in transport accident; Car occupant injured in transport accident; Occupant of pick-up truck or van injured in transport accident; Occupant of heavy transport vehicle injured in transport accident; Bus occupant injured in transport accident; Other land transport accidents; Water transport accidents; Air and space transport accidents; Other and unspecified transport accidents; Slipping, tripping, stumbling and falls; Exposure to inanimate mechanical forces; Exposure to animate mechanical forces; Accidental non-transport drowning and submersion; Exposure to electric current, radiation and extreme ambient air temperature and pressure; Exposure to smoke, fire and flames; Contact with heat and hot substances; Exposure to forces of nature; Overexertion and strenuous or repetitive movements; Accidental exposure to other specified factors; Intentional self-harm; Assault; Event of undetermined intent; Legal intervention, operations of war, military operations, and terrorism; Misadventures to patients during surgical and medical care; Medical devices associated with adverse incidents in diagnostic and therapeutic use; Surgical and other medical procedures as the cause of abnormal reaction of the patient, or of later complication, without mention of misadventure at the time of the procedure; Supplementary factors related to causes of morbidity classified elsewhere
21. Factors influencing health status and contact with health services. Sections: Persons encountering health services for examinations; Genetic carrier and genetic susceptibility to disease; Resistance to antimicrobial drugs; Estrogen, and other hormones and factors receptor status; Retained foreign body fragments; Hormone sensitivity malignancy status; Persons with potential health hazards related to communicable diseases; Persons encountering health services in circumstances related to reproduction; Encounters for other specific health care; Persons with potential health hazards related to socioeconomic and psychosocial circumstances; Do not resuscitate status; Blood type; Body mass index [BMI]; Persons encountering health services in other circumstances; Persons with potential health hazards related to family and personal history and certain conditions influencing health status
22. Codes for special purposes. Sections: Provisional assignment of new diseases of uncertain etiology or emergency use
```

Model answer:

```json
{"selected": [13, 4]}
```

### Call 7 — right knee joint space narrowing: choose sections

User message (patient line and note as above, then):

```text
Diagnosis to code: right knee joint space narrowing
Evidence: הממצא המחזק: צילום מראה היצרות של המרווח המפרקי בברך ימין

Options:
1. Infectious arthropathies [chapter: Diseases of the musculoskeletal system and connective tissue]. Includes: Pyogenic arthritis; Direct infections of joint in infectious and parasitic diseases classified elsewhere; Postinfective and reactive arthropathies
2. Autoinflammatory syndromes [chapter: Diseases of the musculoskeletal system and connective tissue]. Includes: Autoinflammatory syndromes
3. Inflammatory polyarthropathies [chapter: Diseases of the musculoskeletal system and connective tissue]. Includes: Rheumatoid arthritis with rheumatoid factor; Other rheumatoid arthritis; Enteropathic arthropathies; Juvenile arthritis; Chronic gout; Gout; Other crystal arthropathies; Other and unspecified arthropathy; Other arthritis; Arthropathies in other diseases classified elsewhere
4. Osteoarthritis [chapter: Diseases of the musculoskeletal system and connective tissue]. Includes: Polyosteoarthritis; Osteoarthritis of hip; Osteoarthritis of knee; Osteoarthritis of first carpometacarpal joint; Other and unspecified osteoarthritis
5. Other joint disorders [chapter: Diseases of the musculoskeletal system and connective tissue]. Includes: Acquired deformities of fingers and toes; Other acquired deformities of limbs; Disorder of patella; Internal derangement of knee; Other specific joint derangements; Other joint disorder, not elsewhere classified
6. Dentofacial anomalies [including malocclusion] and other disorders of jaw [chapter: Diseases of the musculoskeletal system and connective tissue]. Includes: Dentofacial anomalies [including malocclusion]; Other diseases of jaws
… (24 more options)
```

Model answer:

```json
{"selected": [4]}
```

### Call 8 — right knee joint space narrowing: choose final code

User message (patient line and note as above, then):

```text
Diagnosis to code: right knee joint space narrowing
Evidence: הממצא המחזק: צילום מראה היצרות של המרווח המפרקי בברך ימין

Options:
0. none of these codes fits
1. M15.0 Primary generalized (osteo)arthritis
2. M15.1 Heberden's nodes (with arthropathy)
3. M15.2 Bouchard's nodes (with arthropathy)
4. M15.3 Secondary multiple arthritis
5. M15.4 Erosive (osteo)arthritis
… (19 more options)
25. M17.11 Unilateral primary osteoarthritis, right knee
… (73 more options)
```

Model answer:

```json
{"choice": 25, "confidence": "high"}
```

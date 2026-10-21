the goal was to identify the ICD code for the visits, each code with a confidence score of how sure we are about it.
the data is 600 visits, out of which 510 were labeled by three doctors. if a code have only one doctor labeled it so it's dropped. I did it per visit + code pair.
there are hundreds of different codes and many of them have only one visit that got it as a label.
the approach:
I wanted a simple solution that is local and could work offline so i chose QWEN models 
because there are tens of thousands of codes in the ICD data i couldn't send all of them to the model to choose from and I used the ICD hierarchy for the code.
The flow for one visit:
1st llm call: we first ask for the diagnoses and the text of it in the visit text as evidence
2nd call: then for each diagnosis we send the full note, diagnosis and evidence and ask for up to 3 chapters per diagnosis
3rd call: then for each diagnosis  we send the full note, diagnosis and evidence and ask for section from the section list in the chapters we got from 2nd call.
4th call: then for each diagnosis, only if the section have more than 100 codes in all sections combined, we send the full note, diagnosis and evidence and ask it to choose up to 3 categories from the combined category list in those sections. if its a small list of codes (100 codes or fewer) we skip this part.
5th call: then for each diagnosis, only if the categories have more than 100 codes combined we ask for up to 3 sub-categories
6th call: for every diagnosis we send all the codes in the sections \ categories \ sub-categories + "none fits"  with the full note, diagnosis and evidence and ask it to choose one final code with a confidence score

then we check each visit we check the code if it's actually in the ICD code list, if not - we delete it and say "none fits"
then we dedup codes per visit and keep the higher score per code


experiments:
first i tried sending all sections at once and it gave bad results so i added the chapter selection first, it helped significantly, raised section recall from 0.32 to 0.60 on the dev set.
then i found out that the Qwen3-4b is having a hard time with the Hebrew text so i tested the Qwen 3.5-9b with same exact architecture and the F1 score jumped from 0.29 to 0.46 with the larger model on the test set.

the 9B is better, but the 4B is lighter and faster, especially in docker, which on a mac runs on CPU only. switching is one variable.

limitations and conclusions:
the larger model is more precise but is significantly slower to run.
since the codes are pruned in every step by chapters, sections, categories and sub-categories, if we lose the correct code in each step we can't bring it back in later steps.
the confidence scores are not calibrated.
the visits notes seem to be repetitive so I'm not sure how this mechanism will perform in real life scenarios.

main conclusion is that using the ICD code hierarchy is allowing me to simplify the problem from a tens of thousands multi label classification to a few steps of tens of categories classifications but each step of classification is affecting the following steps and the final results (more places to make mistakes but easier steps)

evaluation:
I split the labeled visits into dev (used only to compare designs and models) and test (run once at the end, on the same 100 visits for both models). The main metric is precision, recall and F1 over pairs (visit, code).
For every code the system missed, I tracked at which step it was lost: the model didn't identify that diagnosis in the note, the right chapter or section wasn't chosen, the correct code was dropped while narrowing down the categories, or the correct code was in the final list but the model picked a different one. This showed me which steps cause most of the errors.

Why not KNN. most codes appear only once in the labeled visits, and 77% of the codes in the test set never appear in the dev set. label-based method like KNN or a classifier can't predict codes it has never seen, so I let the model choose from the full official ICD catalog instead.

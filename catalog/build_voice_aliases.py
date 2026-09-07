#!/usr/bin/env python3
"""Generate catalog/voice-aliases.json: the terminology the voice order parser accepts.

    python3 catalog/build_voice_aliases.py

Keyed by CATALOG id, never by case id. The engine resolves a catalog id to whatever
the bound case calls it through the pack's binding map, exactly as the action grid
does, so a case that renames an entry needs nothing here.

Every phrase is normalised by the same pipeline the parser applies to a transcript
(engine/voice.js: lowercase, punctuation dropped, token canonicalisation, filler
words removed), so a phrase may be written the way a resident says it. Four kinds:

  aliases      phrase -> one catalog id
  expansions   phrase -> several catalog ids, all ordered ("CMP", "MTP", "DuoNeb")
  ambiguous    phrase -> several catalog ids, the resident picks one ("magnesium")
  unavailable  phrase -> a hint, for something residents say that the catalog lacks

Nothing here is a clinical judgement. It records what a phrase MEANS, not whether
ordering it is right, and a phrase that could mean two orders is listed as ambiguous
rather than resolved in favour of the more common one. The two exceptions are stated
by the author: "calcium" is the calcium level only, and "CMP" is the Chem 7 plus the
hepatic panel.

The parser also derives phrases from every catalog display name ("XR - Chest" gives
"xr chest" and "chest xr"; "(CBC)" gives "cbc"), so an entry with no row here is still
orderable by its button name. Rows here are the OTHER ways of saying it.
"""
import json, os, sys, collections, re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "voice-aliases.json")
CATALOG = json.load(open(os.path.join(HERE, "action-catalog.json")))
IDS = {e["id"] for e in CATALOG["entries"]}

A = collections.defaultdict(list)     # aliases
EXPAND, AMBIG, UNAVAIL = {}, {}, {}


def alias(cid, *phrases):
    assert cid in IDS, cid
    A[cid].extend(phrases)


def expand(phrase, *cids):
    for c in cids: assert c in IDS, c
    EXPAND[phrase] = list(cids)


def ambiguous(phrase, *cids):
    for c in cids: assert c in IDS, c
    AMBIG[phrase] = list(cids)


def unavailable(phrase, hint):
    UNAVAIL[phrase] = hint


# ---------------------------------------------------------------- normalisation
# The pipeline the parser applies to speech, written once here and once in
# engine/voice.js. The two must agree: engine-tests.js asserts that normalising every
# phrase in the emitted file with the JS pipeline returns it unchanged, so a change to
# either side without the other fails the build's tests rather than the resident's order.
#
#   1. lower-case; every run of characters that is not a letter or digit becomes one space
#   2. number words become digits, token by token
#   3. the regular-expression canon rules below run in order over the spaced string
#   4. filler words, unit words and bare numbers are dropped, token by token
NUMBER_WORDS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
                "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14",
                "fifteen": "15", "sixteen": "16", "seventeen": "17", "eighteen": "18", "nineteen": "19", "twenty": "20",
                "thirty": "30", "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70", "eighty": "80", "ninety": "90",
                "hundred": "100", "thousand": "1000", "oh": "0"}
# Each rule is [pattern, replacement]; patterns are matched against the whole spaced
# string with word boundaries added on both sides, so they are written without them.
# Replacements are single tokens (letters only) so the next stage cannot drop them.
CANON = [
    # stopping an infusion
    [r"(discontinue|d c|dc|turn off|shut off|wean off|come off|take off|hold|kill)", "stop"],
    # head of the bed, before the rate rule can eat "at 30"
    [r"(head of bed up|head of the bed up|hob up|head of bed 30|head of bed at 30|head of bed to 30|head of the bed 30|head of the bed at 30|head of the bed to 30|hob 30|hob at 30|hob to 30|head of bed 45|hob 45|raise the head of the bed|raise the head of bed|elevate the head of the bed|elevate the head of bed|sit the patient up|sit them up|sit him up|sit her up|sit up|sit upright|upright|high fowlers|semi fowlers|fowlers|semi recumbent|reverse trendelenburg|reverse trendelenberg|reverse t burg|legs up|raise the legs|elevate the legs|passive leg raise|leg raise|p l r|plr)", "headup"],
    # rates first, so "at 250" is a rate and not a quarter litre
    [r"at [0-9]+( cc| ml| cc s)?( an hour| per hour| hourly| an hr| per hr)?", "rate"],
    [r"[0-9]+ (cc|ml) (an hour|per hour|hourly)", "rate"],
    # volumes; the bare numbers 500 and 250 survive only beside a fluid word or a bolus word
    [r"(1 liter|1 l|1l|1000 cc|1000 ml|1000 cc s|a liter|1 liters|one liters)", "liter"],
    [r"(2 liters|2 liter|2 l|2l|2000 cc|2000 ml)", "twoliters"],
    [r"(15 liters|15 liter|15 l|15l)", "fifteenliters"],
    [r"(4 liters|4 liter|4 l|4l|6 liters|6 liter|6 l|6l|3 liters|5 liters)", "someliters"],
    [r"(500 cc|500 ml|500 cc s|half a liter|half liter|half of a liter)", "halfliter"],
    [r"(250 cc|250 ml|quarter liter)", "quarterliter"],
    [r"500 (of )?(saline|lr|bolus|d5)", r"halfliter \2"], [r"(saline|lr|bolus|d5) 500", r"\1 halfliter"],
    [r"250 (of )?(saline|lr|bolus|d5)", r"quarterliter \2"], [r"(saline|lr|bolus|d5) 250", r"\1 quarterliter"],
    [r"(30 cc per kilo|30 ml per kilo|30 per kilo|30 cc per kg|30 ml per kg|30 per kg|30 cc kg|30 ml kg|30 per kilogram|30 cc per kilogram|30 ml per kilogram)", "thirtyperkilo"],
    # fluid names
    [r"(normal saline|sodium chloride|0 9 saline|0 9 normal saline|0 9 percent saline|0 9 percent sodium chloride|point 9 saline|ns|n s)", "saline"],
    [r"(lactated ringers|lactated ringer s|lactated ringer|ringers lactate|ringer lactate|ringers|l r)", "lr"],
    [r"(half normal saline|half normal|0 45 saline|0 45 normal saline|0 45|point 45|1 2 saline|1 2 normal saline|half saline)", "halfnormal"],
    [r"d 5", "d5"], [r"d 50", "d50"], [r"d 10", "d10"], [r"d 25", "d25"], [r"d5 w", "d5w"], [r"d10 w", "d10w"],
    # infusion words and rates
    [r"(infusion|gtt|g t t|drips|infusions)", "drip"],
    [r"(at maintenance|maintenance rate|at a maintenance rate|maintenance fluids|maintenance fluid|maintenance ivf|m ivf|mivf|maintenance iv fluids)", "maintenance"],
    [r"(keep vein open|k v o|kvo|t k o|tko|to keep open)", "kvo"],
    [r"wide open", "wideopen"],
    # investigations
    [r"(ekg|e k g|electrocardiogram|electrocardiograph|electrocardiography|e c g)", "ecg"],
    [r"(12 lead|12 leads|twelve leads)", "twelvelead"],
    [r"(x ray|xray|x rays|xrays|radiograph|radiographs|plain film|plain films|film|films|x r)", "xr"],
    [r"(cat scan|ct scan|c t scan|c t|cat)", "ct"],
    [r"(ct angio|ct angiogram|ct angiography|c t a)", "cta"],
    [r"(pocus|sono|sonogram|sonography|ultrasonography|ultra sound|u s)", "ultrasound"],
    [r"(chem 7|chem seven|chem7|chemistry 7)", "chemseven"],
    [r"(type and screen|type screen|t and s|t s|type and cross|type and crossmatch|type cross|t and c|type and hold|group and save|group and screen|type and cross match)", "typeandscreen"],
    [r"(cross match|crossmatch|cross matched|crossmatched)", "crossmatch"],
    [r"(h and h|h h|hemoglobin and hematocrit|hemoglobin hematocrit)", "hemoglobin"],
    [r"(pt and inr|pt inr|pt ptt inr|pt ptt|pt and ptt|pt and ptt and inr|inr and ptt|p t|i n r|p t t|a p t t)", "coags"],
    [r"(d dimer|ddimer|d dimers|d dimers)", "ddimer"],
    [r"(pro bnp|nt pro bnp|nt probnp|n t pro bnp|b n p|b type natriuretic peptide|brain natriuretic peptide|natriuretic peptide)", "bnp"],
    [r"(hs troponin|hs trop|high sensitivity troponin|high sensitivity trop|troponin t|troponin i|trop t|trop i|tropes|trops|trop)", "troponin"],
    [r"(u a|urine analysis|urinalysis with microscopy|ua with micro|urine dip|urine dipstick|dipstick)", "urinalysis"],
    [r"(fingerstick|finger stick|d stick|dstick|dex stick|dextro stick|dextrostick|accu check|accucheck|accuchek|poc glucose|point of care glucose|capillary glucose|capillary blood glucose|fsbs|fsbg|cbg|bedside glucose|glucose check|sugar check|check sugar|blood sugar|blood glucose|fingerstick glucose|fingerstick blood sugar|fingerstick sugar|bedside sugar|poc sugar)", "fingerstick"],
    [r"(v b g|venous gas|venous blood gas|venous resuscitation panel|venous resus panel|resuscitation panel|resus panel)", "vbg"],
    [r"(a b g|arterial gas|arterial blood gas|art gas)", "abg"],
    [r"(ionized calcium|ionised calcium|calcium ionized|calcium ionised|i cal|ical|ica|ionized ca|free calcium)", "ionizedcalcium"],
    [r"(lft s|lfts|lft|liver function tests|liver function test|liver function|hepatic function panel|hepatic panel|hepatic function|liver panel|liver enzymes|liver tests|hfp|transaminases|ast alt|ast and alt)", "lfts"],
    [r"(comprehensive metabolic panel|comprehensive metabolic|complete metabolic panel|chem 14|chem 12|chem 20|c m p)", "cmp"],
    [r"(basic metabolic panel|basic metabolic|basic chemistry|electrolyte panel|electrolytes|lytes|metabolic panel|renal panel|renal function panel|renal function|chem panel|b m p|bmp)", "chemseven"],
    [r"(complete blood count|blood count|cbc with diff|cbc with differential|cbc diff|cbcd|cbc without diff|c b c)", "cbc"],
    [r"(mag level|magnesium level|serum magnesium|serum mag|mg level)", "magnesiumlevel"],
    [r"(mag sulfate|magnesium sulfate|magnesium sulphate|mag sulphate|mgso4|mg so4)", "magnesiumsulfate"],
    [r"mag", "magnesium"],
    [r"(covid 19|sars cov 2|sars cov2|coronavirus|corona)", "covid"],
    [r"(influenza a and b|flu a and b|influenza)", "flu"],
    [r"(procal|procalcitonin|p c t)", "procalcitonin"],
    [r"(sed rate|erythrocyte sedimentation rate|sedimentation rate|e s r)", "esr"],
    [r"(c reactive protein|creactive protein|c r p)", "crp"],
    [r"(creatine kinase|creatinine kinase|creatine phosphokinase|cpk|c k)", "ck"],
    [r"(lactate dehydrogenase|l d h)", "ldh"],
    [r"(lactic acid|lactic|serum lactate|lactate level|lactic acid level)", "lactate"],
    [r"(urine tox screen|urine tox|u tox|utox|urine drug screen|drug screen|toxicology screen|urine toxicology|drugs of abuse|drug panel|u d s|uds|tox screen)", "toxscreen"],
    [r"(quant hcg|quantitative hcg|serum hcg|beta hcg|hcg quant|serum pregnancy test|serum pregnancy|beta quant|quantitative beta|quantitative pregnancy test|serum beta|hcg level|beta hcg quantitative|quantitative beta hcg|h c g quant|quant)", "serumhcg"],
    [r"(urine hcg|urine pregnancy test|urine pregnancy|u p t|upt|u c g|ucg|u hcg|pregnancy test|preg test|qualitative hcg|urine beta|urine preg)", "urinehcg"],
    [r"(ethanol level|etoh level|alcohol level|blood alcohol level|blood alcohol|serum alcohol|b a l|e t o h|etoh|ethanol)", "ethanol"],
    [r"(acetaminophen level|tylenol level|apap level|paracetamol level)", "acetaminophenlevel"],
    [r"(salicylate level|aspirin level|asa level|salicylate aspirin level|salicylates|salicylate)", "salicylatelevel"],
    [r"(t s h|thyroid function tests|thyroid function|thyroid panel|thyroid studies|thyroid stimulating hormone|tfts|tft)", "tsh"],
    [r"(blood cultures times 2|blood cultures x2|blood cultures x 2|two blood cultures|2 blood cultures|blood cx|bcx x2|bcx|cultures times 2|cultures x2|cultures x 2|two sets of blood cultures|2 sets of blood cultures|blood cultures two sets|blood cultures 2 sets|cultures two sets|cultures 2 sets|peripheral cultures|blood cultures|blood culture)", "bloodcultures"],
    [r"(urine culture|urine cx|u cx|ucx|urine cultures)", "urineculture"],
    [r"(c s f|spinal fluid)", "csf"],
    [r"(lumbar puncture|spinal tap|l p)", "lp"],
    [r"(b type|n t)", ""],
    # imaging
    [r"(c spine|cervical spine|cervical)", "cspine"], [r"(l spine|lumbar spine|lumbosacral spine|ls spine|l s spine|lumbar|low back)", "lspine"],
    [r"(t spine|thoracic spine|thoracic)", "tspine"], [r"(head and neck|head neck)", "headandneck"],
    [r"(abdomen and pelvis|abdomen pelvis|a and p|abd pelvis|abd|belly|abdominal|abdomen)", "abdomen"],
    [r"(pulmonary embolus|pulmonary embolism|pulmonary angiogram|pulmonary angiography|p e|pe protocol|pe study|ctpa|ct pa)", "pe"],
    [r"(noncontrast|non contrast|noncon|non con|without contrast|no contrast|dry|non contrasted|noncontrasted)", "noncontrast"],
    [r"(with contrast|contrasted|with iv contrast|w contrast)", "contrast"],
    [r"(m r i|magnetic resonance|magnetic resonance imaging)", "mri"], [r"(m r a|mr angiography|mr angiogram|magnetic resonance angiography)", "mra"],
    [r"(brain|head)", "head"], [r"(chest|thorax|lungs|lung)", "chest"], [r"(cardiac|heart|echocardiogram|echocardiography|transthoracic echo|bedside echo|t t e|tte|echo)", "cardiac"],
    [r"(right upper quadrant|r u q|ruq|gallbladder|biliary|hepatobiliary|liver)", "ruq"],
    [r"(lower extremity venous|lower extremity venous duplex|lower extremity duplex|lower extremity doppler|lower extremity dopplers|leg doppler|leg dopplers|venous duplex|dvt study|dvt scan|dvt|d v t|compression|two point compression|duplex|lower extremity|lower extremities|legs|leg|venous)", "dvt"],
    [r"(soft tissue|abscess|cellulitis|skin)", "softtissue"], [r"(renal|kidney|kidneys|hydro|hydronephrosis)", "renal"],
    [r"(aorta|aortic|abdominal aorta|triple a|a a a|aaa)", "aorta"], [r"(fast exam|fast scan|e fast|efast|extended fast|trauma)", "fast"],
    [r"(dissection protocol|dissection|aortogram|aortagram)", "aorta"],
    [r"(stroke protocol|code stroke|code stroke imaging|perfusion)", "headandneck"],
    [r"(stone protocol|renal stone|kub|kidney stone|stone)", "abdomen"],
    [r"(pelvis|pelvic|hip|hips)", "pelvis"],
    # stabilisation
    [r"(nasal cannula|nasal canula|n c|nasal prongs|nasal oxygen|nasal o2|cannula)", "nc"],
    [r"(non rebreather mask|nonrebreather mask|non rebreather|nonrebreather|non re breather|n r b|nrbm|reservoir mask|oxygen mask|o2 mask)", "nrb"],
    [r"(bi pap|bipap|c pap|cpap|n i v|niv|nippv|nppv|noninvasive ventilation|non invasive ventilation|noninvasive positive pressure ventilation|non invasive positive pressure ventilation|noninvasive positive pressure|non invasive positive pressure|bilevel positive airway pressure|continuous positive airway pressure|bilevel|bi level|noninvasive|non invasive|avaps)", "niv"],
    [r"(bag valve mask|b v m|bvm|bag mask|ambu bag|ambu|self inflating bag|bag valve)", "bvm"],
    [r"(intraosseous|inter osseous|interosseous|i o|io access|ez io|easy io|io line|io needle)", "io"],
    [r"(peripheral iv|i v|iv access|iv line|peripheral line|peripheral access|venous access|large bore iv|large bore access|large bore|18 gauge|16 gauge|20 gauge|14 gauge|22 gauge|antecubital|p i v|piv|iv cannula|iv catheter|venflon)", "iv"],
    [r"(second|another|additional|one more|1 more|2nd|other arm|number 2|number two)", "second"],
    [r"(central venous catheter|central venous access|central venous line|central access|central line|c v c|cvc|c v l|cvl)", "centralline"],
    [r"(triple lumen catheter|triple lumen central line|triple lumen line|triple lumen cvc|multi lumen catheter|t l c|tlc|triple lumen)", "triplelumen"],
    [r"(cordis introducer|introducer sheath|sheath introducer|swan introducer|introducer|mac line|mac catheter|trauma line|resuscitation line|cordis)", "cordis"],
    [r"(arterial line|art line|a line|arterial catheter|arterial access|radial line|femoral arterial|radial arterial)", "artline"],
    [r"(attach monitor|cardiac monitor|monitor leads|telemetry|tele|continuous monitoring|cardiac monitoring|full monitoring|monitors|monitoring|on the monitor|hook up the monitor|hook up to the monitor|connect the monitor|put on the monitor)", "monitor"],
    [r"(pulse ox|pulse oximetry|pulse oximeter|sat probe|sats probe|o2 sat probe)", "monitor"],
    [r"(defib pads|defibrillator pads|defibrillation pads|pacer pads|pacing pads|multifunction pads|multi function pads|hands free pads|electrode pads|zoll pads|lifepak pads)", "pads"],
    [r"(place pads|pads on|put on pads|put pads on|put the pads on|place the pads|get pads on|apply pads|apply the pads|attach pads|attach the pads|connect pads|connect the pads|hook up pads|hook up the pads|pad placement|pads placed|pads in place|pads ready)", "pads"],
    [r"(defibrillator|defibrillate|defibrillation|defib)", "defib"],
    [r"(synchronized cardioversion|synchronised cardioversion|sync cardioversion|synced cardioversion|synchronized shock|synchronised shock|synced shock|sync shock|cardioversion|cardiovert|synchronize|synchronise|synchronized|synchronised|synced|sync|d c c v|dccv|dc cardioversion|electrical cardioversion)", "cardiovert"],
    [r"(unsynchronized|unsynchronised|unsynced|unsync|un synchronized|non synchronized|not synchronized)", "unsynced"],
    [r"(transcutaneous pacing|transcutaneous pacer|external pacing|external pacer|t c p|tcp|cardiac pacing|electrical pacing|pacing|pacer|pacemaker|transvenous pacing|transvenous pacer|transvenous pacemaker|t v p|tvp|temporary pacemaker|temporary pacing|temporary pacer|pace)", "pacing"],
    [r"(chest compressions|compressions|c p r|cpr|cardiopulmonary resuscitation|start the code|run the code|code blue|call a code|code the patient|cardiac massage|external cardiac massage|closed chest massage|b l s|bls|basic life support|a c l s|acls|advanced cardiac life support|advanced cardiovascular life support)", "cpr"],
    [r"(rapid sequence intubation|rapid sequence induction|rapid sequence|r s i|rsi|endotracheal intubation|orotracheal intubation|intubation|intubate|secure the airway|definitive airway)", "intubate"],
    [r"(pre oxygenate|preoxygenate|pre oxygenation|preoxygenation|pre ox|preox|denitrogenate|denitrogenation|apneic oxygenation|apnoeic oxygenation|apox|ap ox|nitrogen washout)", "preox"],
    [r"(cricothyrotomy|cricothyroidotomy|surgical airway|surgical cric|needle cric|scalpel bougie|scalpel finger bougie|front of neck access|f o n a|fona|cut the neck|emergency surgical airway|quicktrach|cric)", "cric"],
    [r"(endotracheal tube|et tube|e t t|ett|e t tube)", "ett"],
    # drugs
    [r"(epinephrine|adrenaline|adrenalin|epi)", "epi"], [r"(norepinephrine|nor epinephrine|noradrenaline|noradrenalin|levophed|levafed|norepi|levo)", "norepi"],
    [r"(phenylephrine|neosynephrine|neo synephrine|neo)", "phenylephrine"], [r"(vasopressin|pitressin|vasostrict|vaso)", "vasopressin"],
    [r"(dobutamine|dobutrex|dobuta)", "dobutamine"], [r"(dopamine|intropin|dopa)", "dopamine"], [r"(esmolol|brevibloc)", "esmolol"],
    [r"(nicardipine|cardene)", "nicardipine"], [r"(nitroprusside|sodium nitroprusside|nipride|s n p)", "nitroprusside"],
    [r"(labetalol|trandate|normodyne)", "labetalol"], [r"(nitroglycerin|nitroglycerine|glyceryl trinitrate|n t g|ntg|nitro|tridil|nitrates|nitrate)", "nitro"],
    [r"(sublingual|s l|under the tongue|tab|tabs|tablet|tablets|spray|nitrostat|nitrolingual)", "sublingual"],
    [r"(alteplase|activase|t p a|tpa|thrombolytics|thrombolytic|thrombolysis|thrombolyse|thrombolyze|lytics|lytic|lyse|fibrinolytics|fibrinolytic|fibrinolysis|clot buster|clot busters|cathflo)", "tpa"],
    [r"(tenecteplase|tnkase|t n k|tnk)", "tnk"], [r"(adenosine|adenocard)", "adenosine"], [r"(amiodarone|cordarone|pacerone|nexterone|amio)", "amiodarone"],
    [r"(apixaban|eliquis)", "apixaban"], [r"(aspirin|acetylsalicylic acid|a s a|asa|baby aspirin|chewable aspirin|ecotrin|bayer|bufferin)", "aspirin"],
    [r"(atorvastatin|lipitor|statin)", "atorvastatin"], [r"(clopidogrel|plavix)", "clopidogrel"], [r"(digoxin|lanoxin|dig)", "digoxin"],
    [r"(diltiazem|cardizem|dilt)", "diltiazem"], [r"(enoxaparin|lovenox|clexane|low molecular weight heparin|l m w h|lmwh)", "enoxaparin"],
    [r"(unfractionated heparin|u f h|ufh|heparin)", "heparin"], [r"(metoprolol|lopressor|toprol|metoprolol tartrate)", "metoprolol"],
    [r"(propranolol|inderal)", "propranolol"], [r"(procainamide|pronestyl|procan)", "procainamide"],
    [r"(albuterol|salbutamol|ventolin|proventil|proair|nebs|neb|nebulizer|nebuliser|nebulizers|nebulisers|breathing treatment|breathing treatments)", "albuterol"],
    [r"(ipratropium|atrovent|ipratropium bromide)", "ipratropium"], [r"(duo neb|duoneb|duonebs|duo nebs|combivent)", "duoneb"],
    [r"(esomeprazole|nexium|proton pump inhibitor|p p i|ppi)", "esomeprazole"], [r"(famotidine|pepcid|h2 blocker|h 2 blocker|h2 antagonist)", "famotidine"],
    [r"(glucagon|glucagen)", "glucagon"], [r"(metoclopramide|reglan)", "metoclopramide"], [r"(octreotide|sandostatin|somatostatin)", "octreotide"],
    [r"(ondansetron|zofran)", "ondansetron"], [r"(acyclovir|zovirax)", "acyclovir"], [r"(amoxicillin|amoxil|amox)", "amoxicillin"],
    [r"(amphotericin b|amphotericin|ambisome|fungizone|ampho b|ampho)", "amphotericin"], [r"(ampicillin|amp)", "ampicillin"],
    [r"(azithromycin|zithromax|azithro|z pak|z pack|zpak|zpack)", "azithromycin"], [r"(aztreonam|azactam)", "aztreonam"],
    [r"(cefazolin|ancef|kefzol)", "cefazolin"], [r"(cefepime|maxipime)", "cefepime"], [r"(cefotaxime|claforan)", "cefotaxime"],
    [r"(ceftriaxone|rocephin|c t x|ctx)", "ceftriaxone"], [r"(chloramphenicol|chloromycetin)", "chloramphenicol"], [r"(ciprofloxacin|cipro)", "ciprofloxacin"],
    [r"(clindamycin|cleocin|clinda)", "clindamycin"], [r"(doxycycline|vibramycin|doxy)", "doxycycline"], [r"(fluconazole|diflucan)", "fluconazole"],
    [r"(gentamicin|garamycin|gent)", "gentamicin"], [r"(levofloxacin|levaquin|levo floxacin)", "levofloxacin"], [r"(meropenem|merrem|mero)", "meropenem"],
    [r"(metronidazole|flagyl)", "metronidazole"], [r"(minocycline|minocin)", "minocycline"], [r"(moxifloxacin|avelox|moxi)", "moxifloxacin"],
    [r"(oseltamivir|tamiflu)", "oseltamivir"], [r"(penicillin g|pen g|aqueous penicillin|aqueous penicillin g|p c n|pcn|penicillin)", "penicillin"],
    [r"(piperacillin tazobactam|piperacillin and tazobactam|pip tazo|piptazo|pip taz|zosyn|tazocin)", "zosyn"], [r"(rifampin|rifampicin|rifadin)", "rifampin"],
    [r"(vancomycin|vancocin|vanco|vanc)", "vancomycin"], [r"(methergine|methylergonovine|methylergometrine)", "methergine"],
    [r"(misoprostol|cytotec)", "misoprostol"], [r"(oxytocin|pitocin|pit)", "oxytocin"], [r"(rhogam|rho gam|rhophylac|winrho|anti d|rh immune globulin|rhig|rho d immune globulin|rhod immune globulin)", "rhogam"],
    [r"(dexamethasone|decadron|dex)", "dexamethasone"], [r"(diphenhydramine|benadryl)", "diphenhydramine"],
    [r"(methylprednisolone|solu medrol|solumedrol|methylpred|medrol)", "methylprednisolone"], [r"(hydrocortisone|solu cortef|solucortef|cortef)", "hydrocortisone"],
    [r"(prednisone|deltasone)", "prednisone"], [r"(activated charcoal|charcoal)", "charcoal"],
    [r"(digoxin immune fab|digifab|digibind|digoxin fab|digoxin fab fragments|digoxin antibody|digoxin antibodies|fab fragments)", "digifab"],
    [r"(flumazenil|romazicon)", "flumazenil"], [r"(fomepizole|antizol|4 methylpyrazole|methylpyrazole|4 m p|4mp|4 mp)", "fomepizole"],
    [r"(intralipid|lipid emulsion|intravenous lipid emulsion|lipid emulsion therapy|lipid rescue|i l e|ile|fat emulsion|lipids|lipid)", "intralipid"],
    [r"(n acetylcysteine|acetylcysteine|n acetyl cysteine|mucomyst|acetadote|n a c|nac)", "nac"],
    [r"(sodium bicarbonate|sodium bicarb|na bicarbonate|na bicarb|nahco3|bicarbonate|bicarb|amp of bicarb|amps of bicarb)", "bicarb"],
    [r"(naloxone|narcan)", "naloxone"], [r"(physostigmine|antilirium|physo)", "physostigmine"], [r"(pralidoxime|protopam|2 pam|2pam|pam|oxime)", "pralidoxime"],
    [r"(thiamine|vitamin b1|vitamin b 1|b1|b 1)", "thiamine"], [r"(haloperidol|haldol)", "haloperidol"], [r"(olanzapine|zyprexa|zydis)", "olanzapine"],
    [r"(ziprasidone|geodon)", "ziprasidone"], [r"(calcium chloride|cacl2|cacl|ca chloride)", "calciumchloride"], [r"(colchicine|colcrys)", "colchicine"],
    [r"(dextrose|glucose)", "dextrose"], [r"(furosemide|frusemide|lasix)", "furosemide"],
    [r"(hypertonic saline|hypertonic)", "hypertonic"], [r"(23 4 percent|23 4|20 3 point 4 percent|20 3 point 4|20 3 4 percent|20 3 4|20 3 percent|23 percent|25 percent|20 5 percent)", "twentythree"],
    [r"(3 percent|three percent)", "threepercent"], [r"(insulin|regular insulin|humulin|novolin|humulin r|novolin r)", "insulin"],
    [r"(levetiracetam|keppra)", "levetiracetam"], [r"(fosphenytoin|fos phenytoin|cerebyx|phenytoin|dilantin)", "fosphenytoin"],
    [r"(mannitol|osmitrol)", "mannitol"], [r"(potassium chloride|k c l|kcl|k cl)", "kcl"], [r"(potassium iodide|s s k i|sski|ski|lugols solution|lugol solution|lugols|lugol|iodide|iodine)", "iodine"],
    [r"(propylthiouracil|p t u|ptu)", "ptu"], [r"(t dap|tdap|d tap|dtap|tetanus toxoid|tetanus shot|tetanus booster|tetanus vaccine|tetanus|td|boostrix|adacel)", "tdap"],
    [r"(tranexamic acid|t x a|txa|cyklokapron|lysteda)", "txa"], [r"(midazolam|versed|midaz)", "midazolam"], [r"(lorazepam|ativan)", "lorazepam"],
    [r"(etomidate|amidate)", "etomidate"], [r"(ketamine|ketalar)", "ketamine"], [r"(propofol|diprivan)", "propofol"],
    [r"(succinylcholine|suxamethonium|anectine|succs|succ|sux)", "succinylcholine"], [r"(rocuronium|zemuron|rock uranium|rockuronium|rocuroneum|roc)", "rocuronium"],
    [r"(lidocaine|xylocaine|lido)", "lidocaine"], [r"(fentanyl|sublimaze)", "fentanyl"], [r"(morphine|morphine sulfate|morphine sulphate|m s)", "morphine"],
    [r"(acetaminophen|tylenol|paracetamol|ofirmev|a p a p|apap)", "acetaminophen"], [r"(ibuprofen|motrin|advil|caldolor|nsaid|nsaids)", "ibuprofen"],
    [r"(prothrombin complex concentrate|prothrombin complex|4 factor pcc|four factor pcc|4 factor|fourfactor|4 f pcc|4fpcc|kcentra|beriplex|octaplex|p c c|pcc)", "pcc"],
    [r"(intravenous immunoglobulin|immunoglobulin|immune globulin|gamma globulin|gammagard|privigen|octagam|flebogamma|gamunex|i v i g|ivig|iv ig)", "ivig"],
    [r"(factor 8|factor viii|factor v i i i|advate|kogenate|humate p|humate|alphanate|koate|hemofil|novoeight|eloctate|adynovate|xyntha|recombinate)", "factoreight"],
    [r"(factor 9|factor ix|factor i x|benefix|alprolix|idelvion|rebinyn|rixubis|ixinity|mononine|alphanine|christmas factor)", "factornine"],
    [r"(packed red blood cells|packed red cells|packed cells|red blood cells|red cells|p r b c|prbcs|prbc|rbcs|rbc|units of blood|unit of blood)", "prbc"],
    [r"(fresh frozen plasma|f f p|ffp|plasma)", "ffp"], [r"(platelets|platelet|plts|plt)", "platelets"],
    [r"(transfuse|transfusion)", "transfuse"],
    [r"(massive transfusion protocol|massive transfusion|m t p|mtp|activate mtp|activate massive transfusion|1 1 1|one to one to one|balanced transfusion)", "mtp"],
    [r"(o neg|o negative|o pos|o positive|uncrossmatched|uncrossed|emergency release|type specific|universal donor)", "prbc"],
    [r"(im|i m|intramuscular|intramuscularly)", "im"], [r"(sub q|subq|subcutaneous|subcutaneously|s q|sq)", "im"],
    [r"(intranasal|i n)", "intranasal"], [r"(per rectum|rectal|rectally|p r|suppository)", "rectal"],
    [r"(by mouth|orally|oral|p o|po)", "oral"], [r"(bolus|push|pushed|iv push|slow push|one time|single dose|stat dose)", "bolus"],
    [r"(precautions|precaution|isolation precautions|isolation precaution)", "precautions"],
    [r"(personal protective equipment|p p e|ppe|gown and gloves|gowns and gloves|gown and glove|gown up|gown and glove up|gloves and gown)", "ppe"],
    [r"(nasogastric tube|nasogastric|n g t|ngt|n g|ng tube|ng)", "ngtube"], [r"(orogastric tube|orogastric|o g t|ogt|o g|og tube|og)", "ogtube"],
    [r"(foley catheter|foley|urinary catheter|bladder catheter|urethral catheter|indwelling catheter|indwelling urinary catheter|i d c|idc)", "foley"],
    [r"(chest tube|tube thoracostomy|thoracostomy tube|thoracostomy|pigtail catheter|pigtail chest tube|pigtail|chest drain|intercostal drain)", "chesttube"],
    [r"(c collar|cervical collar|hard collar|aspen collar|miami j collar|miami j|philadelphia collar|collar)", "ccollar"],
    [r"(whole bowel irrigation|w b i|wbi|bowel irrigation|golytely|go lytely)", "wbi"],
    [r"(decontaminate|decontamination|decon|hazmat activation|activate hazmat|hazmat)", "decon"],
    [r"(lower head of bed|lower the head of the bed|head of bed down|head of the bed down|lay flat|lie flat|lay the patient flat|lie the patient flat|supine|hob flat|hob down|head of bed flat|flatten the bed|bed flat|lay down|lie down)", "layflat"],
    [r"(sniffing position|ear to sternal notch|ramp the patient|ramped position|ramped|ramping|ramp|shoulder roll|position for intubation|position the patient for intubation|positioning for intubation|position for airway|position for the airway|position for laryngoscopy|position for rsi|position for intubate|position for the tube)", "positionforintubation"],
    [r"(warming measures|rewarming|rewarm|warming|warm the patient|bair hugger|bear hugger|forced air warming|forced air warmer|warm blankets|warm blanket|warmed blankets|warmed fluids|warm fluids|warm iv fluids|warmed iv fluids|fluid warmer|heat lamps|heat lamp|warming lights|radiant warmer|hypothermia protocol|active rewarming|passive rewarming|external rewarming)", "warming"],
    [r"(cooling measures|cooling|cool the patient|active cooling|external cooling|evaporative cooling|ice packs|ice pack|cold packs|cooling blanket|cooling blankets|arctic sun|cooling pads|cooling catheter|cooling vest|cold saline|cold normal saline|iced saline|chilled saline|ice water immersion|cold water immersion|ice bath|mist and fan|misting and fanning|hyperthermia protocol|heat stroke protocol|heatstroke protocol|targeted temperature management|t t m|ttm|therapeutic hypothermia|induced hypothermia)", "cooling"],
    [r"(droplet precautions|droplet precaution|droplet isolation|droplet)", "droplet"], [r"(contact precautions|contact precaution|contact isolation|enteric precautions|enteric isolation|enteric|contact)", "contactprecautions"],
    [r"(airborne precautions|airborne precaution|airborne isolation|negative pressure room|negative pressure isolation|negative pressure|n 95|n95|papr|tb precautions|tuberculosis precautions|tb isolation|airborne)", "airborne"],
    [r"(isolation room|isolate the patient|isolate them|isolate him|isolate her|isolate|isolation|private room|single room)", "isolation"],
    [r"(peak flow meter|peak expiratory flow meter|peak expiratory flow|peak flow|p e f r|pefr|pef|spirometry)", "peakflow"],
    [r"(handheld doppler|doppler pulses|doppler pulse check|pulse doppler|dopplers|doppler)", "doppler"],
    [r"(c reactive|reactive protein)", "crp"],
]
FILLERS = set("a an the of please thank thanks get give order start send check draw obtain some me let lets i want would like need we also do can could you put place go ahead and then plus with to on in by at into onto his her him them their they it its this that these those is are be will shall should just really now stat asap urgently urgent quickly quick immediately right away okay ok yes yeah so um uh er hmm well right left patient patients pt pts him her theirs my our your yours us we from off too very".split())
# "left" and "right" are fillers: the catalog has no sided entries. "off" is a filler
# EXCEPT that "X off" is handled by the stop canon before fillers run, see STOPS above.
FILLERS -= {"off"}
FILLERS |= {"hang", "load", "loading", "loaded"}
UNITS = set("mg milligram milligrams mcg microgram micrograms g gram grams gm gms unit units meq milliequivalent milliequivalents cc ccs ml mls milliliter milliliters millilitre millilitres kg kilo kilos kilogram kilograms per hour hours hr hrs minute minutes min mins q every over each dose doses times x mcgs mgs percent iu".split())
UNITS -= {"percent", "every", "each"}

def normalise(text):
    t = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    toks = [NUMBER_WORDS.get(w, w) for w in t.split()]
    t = " ".join(toks)
    # To a fixed point, because one rule's output can be another rule's input ("kidney
    # function" becomes "renal function", which is a Chem 7), and because dropping a
    # filler can bring two words together that a rule names ("oxygen by mask"). Four
    # rounds is far more than any phrase needs; the bound is there so a pair of rules
    # that undo each other cannot hang the build.
    for _ in range(4):
        before = t
        t = " " + t + " "
        for pat, rep in CANON:
            t = re.sub(r"(?<= )" + pat + r"(?= )", rep, t)
            t = re.sub(r" +", " ", t)
        t = " ".join(w for w in t.split() if w not in FILLERS and w not in UNITS)
        if t == before: break
    # Bare numbers go last, so a volume that a rule names ("500 of normal saline") is
    # still there when the fluid name has been reduced to the word the rule expects.
    return " ".join(w for w in t.split() if not re.fullmatch(r"[0-9]+", w))


# Ultrasound. "pocus", "sono", "sonogram" and "us" canonicalise to "ultrasound" in the
# parser, and "of the" is filler, so "pocus of the heart", "cardiac ultrasound" and
# "ultrasound heart" all reduce to one of the two orders written here.
def us(cid, *regions):
    for r in regions:
        alias(cid, f"{r} ultrasound", f"ultrasound {r}")

us("ultrasound_cardiac", "cardiac", "heart", "echo", "bedside echo")
alias("ultrasound_cardiac", "echo", "echocardiogram", "echocardiography", "tte", "bedside echo",
      "transthoracic echo", "cardiac pocus", "rush exam")
us("ultrasound_fast", "fast", "efast", "e fast", "trauma")
alias("ultrasound_fast", "fast", "fast exam", "fast scan", "efast", "e fast", "extended fast")
us("ultrasound_lung", "lung", "lungs", "chest", "pulmonary", "thoracic")
alias("ultrasound_lung", "b lines", "lung sliding")
us("ultrasound_aorta", "aorta", "aortic", "abdominal aorta", "aaa")
alias("ultrasound_aorta", "aaa scan", "aaa screen", "triple a ultrasound", "ultrasound triple a")
us("ultrasound_renal", "renal", "kidney", "kidneys", "bladder", "renal bladder")
alias("ultrasound_renal", "hydro scan", "hydronephrosis ultrasound")
us("ultrasound_ruq", "ruq", "right upper quadrant", "gallbladder", "biliary", "hepatobiliary",
   "liver", "abdominal")
alias("ultrasound_ruq", "gallbladder scan")
us("ultrasound_lower_extremity_venous", "dvt", "leg", "legs", "lower extremity", "lower extremity venous",
   "venous", "venous duplex", "lower extremity doppler", "leg doppler", "compression")
alias("ultrasound_lower_extremity_venous", "dvt study", "dvt scan", "venous duplex", "lower extremity duplex",
      "leg dopplers", "lower extremity dopplers", "dvt ultrasound", "two point compression",
      "duplex", "lower extremity venous duplex")
us("ultrasound_soft_tissue", "soft tissue", "abscess", "skin", "cellulitis")
alias("doppler", "doppler", "handheld doppler", "doppler pulses", "doppler pulse check", "pulse doppler")
ambiguous("ultrasound", "ultrasound_cardiac", "ultrasound_lung", "ultrasound_fast", "ultrasound_aorta",
          "ultrasound_ruq", "ultrasound_renal", "ultrasound_lower_extremity_venous", "ultrasound_soft_tissue")
ambiguous("bedside ultrasound", "ultrasound_cardiac", "ultrasound_lung", "ultrasound_fast", "ultrasound_aorta",
          "ultrasound_ruq", "ultrasound_renal", "ultrasound_lower_extremity_venous", "ultrasound_soft_tissue")
# "cardiopulmonary pocus" is heart and lungs together, which is two orders.
expand("cardiopulmonary ultrasound", "ultrasound_cardiac", "ultrasound_lung")
expand("ultrasound heart lungs", "ultrasound_cardiac", "ultrasound_lung")
expand("heart lung ultrasound", "ultrasound_cardiac", "ultrasound_lung")

# Bedside tests
alias("ecg_12_lead", "ecg", "ekg", "electrocardiogram", "12 lead", "twelve lead", "12 lead ecg", "twelve lead ecg",
      "12 lead ekg", "twelve lead ekg", "ecg 12 lead", "ekg 12 lead", "tracing", "cardiogram", "repeat ecg", "repeat ekg",
      "stat ecg", "stat ekg", "ecg stat", "ekg stat", "another ecg", "another ekg")
alias("fingerstick_blood_sugar", "fingerstick", "finger stick", "fingerstick glucose", "finger stick glucose",
      "fingerstick blood sugar", "point of care glucose", "poc glucose", "accu check", "accucheck", "accuchek",
      "glucose check", "blood sugar", "blood glucose", "sugar check", "check sugar", "dstick", "d stick",
      "dex stick", "dextrostick", "dextro stick", "bedside glucose", "bedside sugar", "poc sugar", "cbg",
      "capillary glucose", "capillary blood glucose", "fsbs", "fsbg", "fingerstick sugar", "sugar")
ambiguous("glucose", "fingerstick_blood_sugar", "d50_bolus")
alias("peak_expiratory_flow_meter", "peak flow", "peak flow meter", "peak expiratory flow", "pefr", "pef",
      "spirometry")

# Lab work
alias("arterial_blood_gas", "abg", "arterial gas", "arterial blood gas", "art gas")
alias("venous_blood_gas", "vbg", "venous gas", "venous blood gas", "venous resuscitation panel",
      "resuscitation panel", "resus panel", "venous resus panel", "blood gas", "gas")
alias("basic_chemistry_chem_7", "chem 7", "chem seven", "chem7", "bmp", "basic metabolic panel", "basic metabolic",
      "basic chemistry", "chemistry", "chem", "lytes", "electrolytes", "electrolyte panel", "chem panel",
      "metabolic panel", "renal panel", "renal function", "renal function panel", "bun creatinine",
      "bun and creatinine", "creatinine", "sodium", "sodium level", "potassium level", "bicarb level",
      "kidney function", "chem 8")
alias("liver_function_tests_lfts", "lft", "lfts", "liver function", "liver function tests", "liver function test",
      "hepatic panel", "hepatic function panel", "hepatic function", "liver panel", "liver enzymes", "liver tests",
      "hfp", "transaminases", "ast alt", "ast and alt", "bilirubin", "alk phos", "hepatic")
expand("cmp", "basic_chemistry_chem_7", "liver_function_tests_lfts")
expand("comprehensive metabolic panel", "basic_chemistry_chem_7", "liver_function_tests_lfts")
expand("comprehensive metabolic", "basic_chemistry_chem_7", "liver_function_tests_lfts")
expand("complete metabolic panel", "basic_chemistry_chem_7", "liver_function_tests_lfts")
expand("chem 14", "basic_chemistry_chem_7", "liver_function_tests_lfts")
expand("chem 12", "basic_chemistry_chem_7", "liver_function_tests_lfts")
expand("chem 20", "basic_chemistry_chem_7", "liver_function_tests_lfts")
alias("calcium_level", "calcium", "calcium level", "total calcium", "serum calcium", "ca level", "ca")
alias("calcium_ionized", "ionized calcium", "ionised calcium", "ical", "i cal", "ica", "calcium ionized",
      "ionized ca", "free calcium")
alias("magnesium_level", "magnesium level", "mag level", "serum magnesium", "serum mag", "mg level",
      "magnesium lab")
alias("phosphate_level", "phosphate", "phosphorus", "phos", "phosphate level", "phosphorus level", "phos level",
      "serum phosphate")
expand("mag phos", "magnesium_level", "phosphate_level")
expand("mag and phos", "magnesium_level", "phosphate_level")
expand("magnesium phosphate", "magnesium_level", "phosphate_level")
expand("magnesium phosphorus", "magnesium_level", "phosphate_level")
alias("complete_blood_count_cbc", "cbc", "complete blood count", "blood count", "cbc with diff", "cbc with differential",
      "cbc diff", "cbc without diff", "hemoglobin", "hemoglobin level", "h and h", "hgb", "h h", "hemoglobin hematocrit",
      "hematocrit", "white count", "wbc", "platelet count", "platelets count", "blood counts", "cbcd")
alias("coagulation_panel", "coags", "coag", "coag panel", "coagulation panel", "coagulation studies", "coagulation",
      "pt inr", "pt ptt", "pt ptt inr", "inr", "pt", "ptt", "aptt", "pt and inr", "pt and ptt", "prothrombin time",
      "clotting studies", "clotting", "coagulation profile", "coag profile", "coagulation tests")
alias("d_dimer", "d dimer", "ddimer", "dimer", "dimers", "d dimers")
alias("lactate", "lactate", "lactic acid", "lactic", "lactate level", "serum lactate", "lactic acid level")
alias("lipase", "lipase", "lipase level")
alias("amylase", "amylase", "amylase level")
alias("blood_type_and_screen", "type and screen", "type screen", "type and cross", "type and crossmatch",
      "crossmatch", "cross match", "type cross", "t and s", "t and c", "blood type", "blood typing", "type",
      "abo", "type and hold", "group and save", "group and screen")
alias("plasma_procalcitonin", "procalcitonin", "procal", "pct")
alias("nt_probnp", "bnp", "pro bnp", "probnp", "nt probnp", "nt pro bnp", "b type natriuretic peptide",
      "brain natriuretic peptide", "natriuretic peptide", "bnp level")
alias("troponin_t", "troponin", "trop", "tropes", "trops", "troponin t", "troponin i", "high sensitivity troponin",
      "hs troponin", "hs trop", "cardiac enzymes", "cardiac markers", "cardiac biomarkers", "troponin level",
      "repeat troponin", "repeat trop", "delta troponin", "delta trop", "trop t", "trop i", "serial troponins")
alias("urinalysis", "ua", "urinalysis", "urine analysis", "urine dip", "urine dipstick", "dipstick", "urine",
      "urine studies", "u a", "ua with micro", "urinalysis with microscopy", "clean catch", "clean catch urine")
expand("ua and culture", "urinalysis", "urine_culture")
expand("ua with culture", "urinalysis", "urine_culture")
expand("urinalysis and culture", "urinalysis", "urine_culture")
expand("ua culture", "urinalysis", "urine_culture")
expand("ua ucx", "urinalysis", "urine_culture")
alias("urine_culture", "urine culture", "ucx", "urine cx", "urine cultures")
alias("blood_culture_x_2", "blood cultures", "blood culture", "blood cultures times two", "blood cultures x2",
      "blood cultures times 2", "two blood cultures", "2 blood cultures", "blood cx", "bcx", "bcx x2", "cultures times two",
      "cultures x2", "cultures times 2", "two sets of blood cultures", "2 sets of blood cultures", "blood cultures two sets",
      "cultures two sets", "peripheral cultures", "cultures")

# Other labs
alias("acetaminophen_level", "acetaminophen level", "tylenol level", "apap level", "paracetamol level")
ambiguous("acetaminophen", "acetaminophen", "acetaminophen_level")
ambiguous("apap", "acetaminophen", "acetaminophen_level")
alias("salicylate_aspirin_level", "salicylate level", "aspirin level", "asa level", "salicylate", "salicylates",
      "salicylate aspirin level")
expand("tylenol and aspirin levels", "acetaminophen_level", "salicylate_aspirin_level")
expand("acetaminophen and salicylate levels", "acetaminophen_level", "salicylate_aspirin_level")
expand("apap and asa", "acetaminophen_level", "salicylate_aspirin_level")
expand("apap asa", "acetaminophen_level", "salicylate_aspirin_level")
expand("acetaminophen salicylate", "acetaminophen_level", "salicylate_aspirin_level")
expand("tylenol aspirin", "acetaminophen_level", "salicylate_aspirin_level")
alias("ethanol_level_etoh", "ethanol level", "etoh level", "etoh", "ethanol", "alcohol level", "blood alcohol",
      "blood alcohol level", "bal", "serum alcohol", "alcohol")
alias("urine_tox_screen", "urine tox", "utox", "u tox", "tox screen", "urine tox screen", "urine drug screen",
      "drug screen", "uds", "toxicology screen", "tox", "urine toxicology", "drugs of abuse", "drug panel")
alias("c_reactive_protein_crp", "crp", "c reactive protein", "creactive protein")
alias("erythrocyte_sedimentation_rate_esr", "esr", "sed rate", "erythrocyte sedimentation rate", "sedimentation rate")
expand("esr and crp", "erythrocyte_sedimentation_rate_esr", "c_reactive_protein_crp")
expand("esr crp", "erythrocyte_sedimentation_rate_esr", "c_reactive_protein_crp")
expand("crp esr", "erythrocyte_sedimentation_rate_esr", "c_reactive_protein_crp")
expand("crp and esr", "erythrocyte_sedimentation_rate_esr", "c_reactive_protein_crp")
expand("inflammatory markers", "erythrocyte_sedimentation_rate_esr", "c_reactive_protein_crp")
alias("creatine_kinase_ck", "ck", "cpk", "creatine kinase", "creatinine kinase", "ck level", "cpk level",
      "total ck", "creatine phosphokinase")
alias("lactate_dehydrogenase_ldh", "ldh", "lactate dehydrogenase")
alias("tsh", "tsh", "thyroid", "thyroid function", "thyroid panel", "thyroid studies", "thyroid stimulating hormone",
      "tfts", "thyroid function tests")
alias("uric_acid", "uric acid", "urate", "uric acid level")
alias("osmolality", "osmolality", "osm", "osms", "serum osm", "serum osmolality", "serum osms", "osmolarity",
      "osmolar gap", "osm gap")
alias("peripheral_smear", "peripheral smear", "smear", "blood smear", "peripheral blood smear", "manual diff",
      "manual differential")
alias("serum_hcg_quantitative", "quant hcg", "quantitative hcg", "serum hcg", "beta hcg", "beta", "quant", "hcg quant",
      "serum pregnancy test", "serum pregnancy", "beta quant", "quantitative beta", "quantitative pregnancy test",
      "serum beta", "hcg level", "beta hcg quantitative", "quantitative beta hcg")
alias("urine_hcg_qualitative", "urine hcg", "urine pregnancy", "urine pregnancy test", "upt", "ucg", "u hcg",
      "pregnancy test", "preg test", "qualitative hcg", "urine beta", "hcg", "urine preg", "pregnancy")
alias("covid_19_test", "covid", "covid test", "covid swab", "covid 19", "covid 19 test", "coronavirus", "corona",
      "sars cov 2", "sars cov2", "covid pcr", "covid antigen", "covid rapid", "rapid covid")
alias("influenza_a_and_b_antigen_test", "flu", "flu swab", "flu test", "influenza", "influenza swab", "influenza test",
      "flu a and b", "influenza a and b", "rapid flu", "flu antigen", "rapid influenza", "flu panel")
expand("flu and covid", "influenza_a_and_b_antigen_test", "covid_19_test")
expand("covid and flu", "influenza_a_and_b_antigen_test", "covid_19_test")
expand("flu covid", "influenza_a_and_b_antigen_test", "covid_19_test")
expand("covid flu", "influenza_a_and_b_antigen_test", "covid_19_test")
alias("csf_cell_count", "csf cell count", "cell count", "csf cells", "spinal fluid cell count")
alias("csf_culture", "csf culture", "spinal fluid culture", "csf cultures")
alias("csf_glucose", "csf glucose", "spinal fluid glucose")
alias("csf_protein", "csf protein", "spinal fluid protein")
alias("csf_gram_stain", "csf gram stain", "gram stain", "spinal fluid gram stain")
alias("csf_rapid_antigen_test_for_n_meningitidis", "csf meningitidis antigen", "csf antigen", "csf rapid antigen",
      "csf meningococcal antigen", "meningitidis antigen", "csf n meningitidis")
expand("csf studies", "csf_cell_count", "csf_glucose", "csf_protein", "csf_gram_stain", "csf_culture")
expand("csf", "csf_cell_count", "csf_glucose", "csf_protein", "csf_gram_stain", "csf_culture")
expand("spinal fluid studies", "csf_cell_count", "csf_glucose", "csf_protein", "csf_gram_stain", "csf_culture")
expand("csf labs", "csf_cell_count", "csf_glucose", "csf_protein", "csf_gram_stain", "csf_culture")
expand("csf analysis", "csf_cell_count", "csf_glucose", "csf_protein", "csf_gram_stain", "csf_culture")
alias("urine_rapid_antigen_test_for_n_meningitidis", "urine meningitidis antigen", "urine meningococcal antigen",
      "urine n meningitidis", "urine meningococcus")
alias("urine_rapid_antigen_test_for_s_pneumoniae", "urine pneumococcal antigen", "urine strep pneumo antigen",
      "pneumococcal antigen", "urine pneumo antigen", "strep pneumo antigen", "urine s pneumoniae", "pneumococcal urine antigen",
      "urinary antigen", "urine antigen", "urine legionella pneumococcal antigen")
alias("skin_biopsy_of_the_rash", "skin biopsy", "biopsy of the rash", "rash biopsy", "punch biopsy", "biopsy")

# Panels and pairs residents say as one phrase. Only NAMED things: a word that stands for a
# fixed set of orders ("CMP", "MTP", "DuoNeb", "DAPT") or an explicit pair ("vanc and zosyn").
# Disease-named bundles ("sepsis workup", "hyperkalemia cocktail") are deliberately absent:
# a parser that turns a diagnosis into its order set is answering the case for the resident.
unavailable("labs", "Name the labs. \"Labs\" on its own is not an order the nurse can send.")
unavailable("basic labs", "Name the labs. \"Basic labs\" means different tubes in different departments.")
unavailable("routine labs", "Name the labs. \"Routine labs\" means different tubes in different departments.")
unavailable("rainbow", "Name the labs. A rainbow draw is a set of tubes, not a set of tests.")
unavailable("rainbow labs", "Name the labs. A rainbow draw is a set of tubes, not a set of tests.")
unavailable("sepsis workup", "Name the studies. The parser does not expand a diagnosis into its workup.")
unavailable("sepsis labs", "Name the labs. The parser does not expand a diagnosis into its workup.")
unavailable("cardiac workup", "Name the studies. The parser does not expand a diagnosis into its workup.")
unavailable("chest pain workup", "Name the studies. The parser does not expand a diagnosis into its workup.")
unavailable("trauma labs", "Name the labs. The parser does not expand a diagnosis into its workup.")
unavailable("tox workup", "Name the studies. The parser does not expand a diagnosis into its workup.")
unavailable("tox labs", "Name the labs. The parser does not expand a diagnosis into its workup.")
unavailable("meningitis workup", "Name the studies. The parser does not expand a diagnosis into its workup.")
unavailable("stroke labs", "Name the labs. The parser does not expand a diagnosis into its workup.")
unavailable("hyperkalemia cocktail", "Name the drugs. The parser does not expand a diagnosis into its treatment.")
unavailable("hyperkalemia treatment", "Name the drugs. The parser does not expand a diagnosis into its treatment.")
unavailable("coma cocktail", "Name the drugs. The parser does not expand a diagnosis into its treatment.")
unavailable("anaphylaxis meds", "Name the drugs. The parser does not expand a diagnosis into its treatment.")
unavailable("meningitis coverage", "Name the antibiotics. The parser does not expand a diagnosis into its treatment.")
unavailable("cap coverage", "Name the antibiotics. The parser does not expand a diagnosis into its treatment.")
unavailable("pneumonia antibiotics", "Name the antibiotics. The parser does not expand a diagnosis into its treatment.")
unavailable("respiratory viral panel", "Flu and COVID are separate tests here; say the ones you want.")
unavailable("viral panel", "Flu and COVID are separate tests here; say the ones you want.")
expand("cbc bmp", "complete_blood_count_cbc", "basic_chemistry_chem_7")
expand("cbc and bmp", "complete_blood_count_cbc", "basic_chemistry_chem_7")
expand("cbc cmp", "complete_blood_count_cbc", "basic_chemistry_chem_7", "liver_function_tests_lfts")
expand("cbc and cmp", "complete_blood_count_cbc", "basic_chemistry_chem_7", "liver_function_tests_lfts")
expand("coags and type and screen", "coagulation_panel", "blood_type_and_screen")
expand("two large bore ivs", "insert_iv", "second_iv")
expand("2 large bore ivs", "insert_iv", "second_iv")
expand("two ivs", "insert_iv", "second_iv")
expand("2 ivs", "insert_iv", "second_iv")
expand("two lines", "insert_iv", "second_iv")
expand("2 lines", "insert_iv", "second_iv")
expand("bilateral ivs", "insert_iv", "second_iv")
expand("two peripheral ivs", "insert_iv", "second_iv")
expand("2 peripheral ivs", "insert_iv", "second_iv")
expand("monitor and iv", "attach_monitor", "insert_iv")
expand("iv and monitor", "attach_monitor", "insert_iv")
expand("iv o2 monitor", "insert_iv", "nasal_cannula_oxygen", "attach_monitor")
expand("iv o2 and monitor", "insert_iv", "nasal_cannula_oxygen", "attach_monitor")
expand("iv oxygen monitor", "insert_iv", "nasal_cannula_oxygen", "attach_monitor")
expand("iv oxygen and monitor", "insert_iv", "nasal_cannula_oxygen", "attach_monitor")
expand("monitor iv oxygen", "attach_monitor", "insert_iv", "nasal_cannula_oxygen")
expand("monitor iv o2", "attach_monitor", "insert_iv", "nasal_cannula_oxygen")
expand("mtp", "transfuse_prbc", "transfuse_ffp", "transfuse_platelets")
expand("massive transfusion", "transfuse_prbc", "transfuse_ffp", "transfuse_platelets")
expand("massive transfusion protocol", "transfuse_prbc", "transfuse_ffp", "transfuse_platelets")
expand("activate mtp", "transfuse_prbc", "transfuse_ffp", "transfuse_platelets")
expand("activate massive transfusion", "transfuse_prbc", "transfuse_ffp", "transfuse_platelets")
expand("one to one to one", "transfuse_prbc", "transfuse_ffp", "transfuse_platelets")
expand("1 1 1", "transfuse_prbc", "transfuse_ffp", "transfuse_platelets")
expand("balanced transfusion", "transfuse_prbc", "transfuse_ffp", "transfuse_platelets")
expand("duoneb", "albuterol", "ipratropium")
expand("duo neb", "albuterol", "ipratropium")
expand("duonebs", "albuterol", "ipratropium")
expand("duo nebs", "albuterol", "ipratropium")
expand("albuterol ipratropium", "albuterol", "ipratropium")
expand("albuterol and ipratropium", "albuterol", "ipratropium")
expand("albuterol and atrovent", "albuterol", "ipratropium")
expand("albuterol atrovent", "albuterol", "ipratropium")
expand("combivent", "albuterol", "ipratropium")
expand("stacked duonebs", "albuterol", "ipratropium")
expand("continuous duoneb", "albuterol", "ipratropium")
expand("vanc and zosyn", "vancomycin", "piperacillin_tazobactam")
expand("vanc zosyn", "vancomycin", "piperacillin_tazobactam")
expand("vanco zosyn", "vancomycin", "piperacillin_tazobactam")
expand("vanco and zosyn", "vancomycin", "piperacillin_tazobactam")
expand("vancomycin and zosyn", "vancomycin", "piperacillin_tazobactam")
expand("vancomycin and piperacillin tazobactam", "vancomycin", "piperacillin_tazobactam")
expand("vanc and cefepime", "vancomycin", "cefepime")
expand("vanc cefepime", "vancomycin", "cefepime")
expand("vanco and cefepime", "vancomycin", "cefepime")
expand("vanco cefepime", "vancomycin", "cefepime")
expand("vancomycin and cefepime", "vancomycin", "cefepime")
expand("vanc and rocephin", "vancomycin", "ceftriaxone")
expand("vanc rocephin", "vancomycin", "ceftriaxone")
expand("vanc and ceftriaxone", "vancomycin", "ceftriaxone")
expand("vancomycin and ceftriaxone", "vancomycin", "ceftriaxone")
expand("ceftriaxone and azithromycin", "ceftriaxone", "azithromycin")
expand("rocephin and azithro", "ceftriaxone", "azithromycin")
expand("rocephin azithro", "ceftriaxone", "azithromycin")
expand("ceftriaxone azithromycin", "ceftriaxone", "azithromycin")
expand("aspirin and heparin", "aspirin", "heparin_bolus_drip")
expand("aspirin heparin", "aspirin", "heparin_bolus_drip")
expand("asa and heparin", "aspirin", "heparin_bolus_drip")
expand("asa heparin", "aspirin", "heparin_bolus_drip")
expand("aspirin and plavix", "aspirin", "clopidogrel")
expand("aspirin plavix", "aspirin", "clopidogrel")
expand("dual antiplatelet", "aspirin", "clopidogrel")
expand("dual antiplatelet therapy", "aspirin", "clopidogrel")
expand("dapt", "aspirin", "clopidogrel")
expand("benadryl and pepcid", "diphenhydramine", "famotidine_bolus")
expand("benadryl pepcid", "diphenhydramine", "famotidine_bolus")
expand("h1 and h2 blockers", "diphenhydramine", "famotidine_bolus")
expand("h1 h2 blockers", "diphenhydramine", "famotidine_bolus")
expand("thiamine and dextrose", "thiamine", "d50_bolus")
expand("thiamine and d50", "thiamine", "d50_bolus")
expand("d50 and thiamine", "d50_bolus", "thiamine")
expand("dextrose and thiamine", "d50_bolus", "thiamine")
expand("thiamine dextrose", "thiamine", "d50_bolus")
expand("thiamine d50", "thiamine", "d50_bolus")
expand("insulin and dextrose", "insulin_bolus", "d50_bolus")
expand("insulin dextrose", "insulin_bolus", "d50_bolus")
expand("insulin and d50", "insulin_bolus", "d50_bolus")
expand("insulin d50", "insulin_bolus", "d50_bolus")
expand("insulin and glucose", "insulin_bolus", "d50_bolus")
expand("insulin glucose", "insulin_bolus", "d50_bolus")
expand("d50 and insulin", "d50_bolus", "insulin_bolus")
expand("etomidate and succinylcholine", "etomidate_bolus", "succinylcholine_bolus")
expand("etomidate and sux", "etomidate_bolus", "succinylcholine_bolus")
expand("etomidate sux", "etomidate_bolus", "succinylcholine_bolus")
expand("etomidate and rocuronium", "etomidate_bolus", "rocuronium_bolus")
expand("etomidate and roc", "etomidate_bolus", "rocuronium_bolus")
expand("etomidate roc", "etomidate_bolus", "rocuronium_bolus")
expand("ketamine and rocuronium", "ketamine_bolus", "rocuronium_bolus")
expand("ketamine and roc", "ketamine_bolus", "rocuronium_bolus")
expand("ketamine roc", "ketamine_bolus", "rocuronium_bolus")
expand("ketamine and sux", "ketamine_bolus", "succinylcholine_bolus")
expand("ketamine and succinylcholine", "ketamine_bolus", "succinylcholine_bolus")
expand("ketamine sux", "ketamine_bolus", "succinylcholine_bolus")
expand("propofol and rocuronium", "propofol_bolus", "rocuronium_bolus")
expand("propofol and roc", "propofol_bolus", "rocuronium_bolus")
expand("propofol roc", "propofol_bolus", "rocuronium_bolus")
expand("fentanyl and versed", "fentanyl_bolus", "midazolam_bolus")
expand("fentanyl and midazolam", "fentanyl_bolus", "midazolam_bolus")
expand("fentanyl versed", "fentanyl_bolus", "midazolam_bolus")
expand("versed and fentanyl", "midazolam_bolus", "fentanyl_bolus")
expand("fentanyl and propofol", "fentanyl_bolus", "propofol_infusion")
expand("droplet and contact precautions", "droplet_precautions", "contact_precautions")
expand("contact and droplet precautions", "contact_precautions", "droplet_precautions")
expand("droplet and contact", "droplet_precautions", "contact_precautions")
expand("contact and droplet", "contact_precautions", "droplet_precautions")
expand("pads and monitor", "place_pads_for_monitoring", "attach_monitor")
expand("monitor and pads", "attach_monitor", "place_pads_for_monitoring")
expand("access and monitor", "insert_iv", "attach_monitor")
expand("monitor and access", "attach_monitor", "insert_iv")

# Imaging. "xray", "x ray", "radiograph", "film" and "plain film" canonicalise to "xr";
# "cat scan" and "ct scan" to "ct"; so "portable chest film" reduces to "portable chest xr".
alias("xr_chest", "chest xr", "xr chest", "cxr", "portable chest", "portable chest xr", "pa and lateral",
      "chest radiograph", "portable cxr", "stat cxr", "repeat cxr", "repeat chest xr", "post intubation cxr",
      "post intubation chest xr", "post procedure cxr", "one view chest", "two view chest", "chest two view",
      "chest one view", "ap chest", "upright chest", "chest film")
alias("xr_pelvis", "pelvis xr", "xr pelvis", "pelvic xr", "pelvis", "ap pelvis", "pelvic film", "pelvis film",
      "pelvic radiograph", "hip xr", "hips xr", "pelvis and hips")
expand("chest and pelvis", "xr_chest", "xr_pelvis")
expand("chest pelvis", "xr_chest", "xr_pelvis")
expand("trauma films", "xr_chest", "xr_pelvis")
expand("trauma series", "xr_chest", "xr_pelvis")
expand("chest and pelvis xr", "xr_chest", "xr_pelvis")
alias("ct_head", "ct head", "head ct", "noncontrast head ct", "non contrast head ct", "noncon head ct", "non con head ct",
      "ct head without contrast", "ct head without", "ct brain", "brain ct", "head scan", "ct of the head", "dry head ct",
      "ct head no contrast", "head ct without contrast", "ct head non contrast", "noncontrast ct head", "ct head noncon")
alias("ct_chest", "ct chest", "chest ct", "ct of the chest", "ct thorax", "ct chest with contrast", "ct chest without contrast",
      "ct chest with", "ct chest without", "chest ct with contrast")
alias("ct_abdomen", "ct abdomen", "abdominal ct", "ct abdomen pelvis", "ct abdomen and pelvis", "ct a p", "ct ap",
      "ct belly", "belly ct", "ct of the abdomen", "ct abdomen with contrast", "ct abdomen without contrast", "ct abd",
      "ct abd pelvis", "abdomen pelvis ct", "ct abdomen pelvis with contrast", "ct abdomen pelvis without contrast",
      "ct stone protocol", "stone protocol ct", "ct renal stone", "ct kub", "ct of the abdomen and pelvis", "ct abdomen with",
      "ct abdomen without", "ct a and p")
alias("ct_c_spine", "ct c spine", "c spine ct", "ct cervical spine", "cervical spine ct", "ct neck", "ct of the c spine",
      "ct cervical", "c spine", "cervical spine imaging")
alias("ct_pulmonary_embolus", "ct pe", "pe ct", "ct pulmonary embolus", "ct pulmonary embolism", "ct angio chest",
      "cta chest", "ct angiogram chest", "ct pulmonary angiogram", "ct pulmonary angiography", "ctpa", "ct pa", "pe study",
      "pe protocol", "pe protocol ct", "ct pe protocol", "ct chest pe protocol", "pulmonary embolism study",
      "ct for pe", "cta for pe", "chest cta", "ct angiography chest", "ct angio of the chest", "cta pe", "pe cta")
alias("ct_aorta", "ct aorta", "cta aorta", "ct angio aorta", "ct angiogram aorta", "ct dissection", "dissection protocol",
      "dissection protocol ct", "ct dissection protocol", "cta dissection", "ct for dissection", "cta for dissection",
      "cta chest abdomen pelvis", "cta chest abdomen and pelvis", "ct angio chest abdomen pelvis", "aortic ct", "ct aortogram",
      "cta aortic", "ct angiography aorta", "ct of the aorta", "aorta ct", "cta chest and abdomen", "ct aorta dissection",
      "cta cap", "ct angio cap", "aortagram", "aortogram", "cta")
alias("ct_cta_head_and_neck", "cta head and neck", "cta head neck", "ct cta head and neck", "ct angio head and neck",
      "ct angiogram head and neck", "cta head", "cta neck", "ct angio head", "ct angio neck", "stroke protocol ct",
      "ct stroke protocol", "code stroke imaging", "code stroke ct", "cta brain", "ct angiography head and neck",
      "ct perfusion", "ct head and neck", "ct and cta head", "ct cta head", "ct cta", "cta head and neck with perfusion",
      "cta of the head and neck", "ct head with cta", "head and neck cta", "head cta")
alias("mri_c_spine", "mri c spine", "c spine mri", "mri cervical spine", "cervical spine mri", "mri cervical", "mri neck")
alias("mri_lumbar_spine", "mri l spine", "l spine mri", "mri lumbar spine", "lumbar spine mri", "mri lumbar", "mri low back",
      "mri lumbosacral", "mri ls spine", "ls spine mri", "mri l s spine", "lumbar mri", "mri back")
alias("mri_thoracic_spine", "mri t spine", "t spine mri", "mri thoracic spine", "thoracic spine mri", "mri thoracic",
      "thoracic mri")
expand("mri total spine", "mri_c_spine", "mri_thoracic_spine", "mri_lumbar_spine")
expand("mri whole spine", "mri_c_spine", "mri_thoracic_spine", "mri_lumbar_spine")
expand("mri entire spine", "mri_c_spine", "mri_thoracic_spine", "mri_lumbar_spine")
expand("mri spine", "mri_c_spine", "mri_thoracic_spine", "mri_lumbar_spine")
expand("total spine mri", "mri_c_spine", "mri_thoracic_spine", "mri_lumbar_spine")
expand("whole spine mri", "mri_c_spine", "mri_thoracic_spine", "mri_lumbar_spine")
alias("mri_mra_head_and_neck", "mri brain", "brain mri", "mri head", "head mri", "mri mra", "mra", "mri mra head and neck",
      "mra head and neck", "mri and mra", "mri of the brain", "mri head and neck", "mri stroke protocol", "mri stroke",
      "diffusion weighted mri", "dwi", "mra head", "mra neck", "mri with mra", "mr angiography", "mr angiogram")
ambiguous("ct", "ct_head", "ct_chest", "ct_abdomen", "ct_c_spine", "ct_pulmonary_embolus", "ct_aorta", "ct_cta_head_and_neck")
ambiguous("ct scan", "ct_head", "ct_chest", "ct_abdomen", "ct_c_spine", "ct_pulmonary_embolus", "ct_aorta",
          "ct_cta_head_and_neck")
ambiguous("mri", "mri_mra_head_and_neck", "mri_c_spine", "mri_thoracic_spine", "mri_lumbar_spine")
ambiguous("xr", "xr_chest", "xr_pelvis")
ambiguous("imaging", "xr_chest", "ct_head", "ct_chest", "ct_abdomen")
ambiguous("ct angio", "ct_pulmonary_embolus", "ct_aorta", "ct_cta_head_and_neck")
ambiguous("ct angiogram", "ct_pulmonary_embolus", "ct_aorta", "ct_cta_head_and_neck")
ambiguous("ct angiography", "ct_pulmonary_embolus", "ct_aorta", "ct_cta_head_and_neck")
ambiguous("ct with contrast", "ct_chest", "ct_abdomen", "ct_pulmonary_embolus", "ct_aorta")
ambiguous("spine ct", "ct_c_spine")
expand("pan scan", "ct_head", "ct_c_spine", "ct_chest", "ct_abdomen")
expand("pan ct", "ct_head", "ct_c_spine", "ct_chest", "ct_abdomen")
expand("trauma pan scan", "ct_head", "ct_c_spine", "ct_chest", "ct_abdomen")
expand("ct head and c spine", "ct_head", "ct_c_spine")
expand("ct head c spine", "ct_head", "ct_c_spine")
expand("ct head and neck", "ct_head", "ct_c_spine")
expand("head and c spine ct", "ct_head", "ct_c_spine")
expand("ct chest abdomen pelvis", "ct_chest", "ct_abdomen")
expand("ct chest abdomen and pelvis", "ct_chest", "ct_abdomen")
expand("ct cap", "ct_chest", "ct_abdomen")
expand("ct chest and abdomen", "ct_chest", "ct_abdomen")
expand("ct c a p", "ct_chest", "ct_abdomen")
expand("ct torso", "ct_chest", "ct_abdomen")
unavailable("ct kidney", "Renal imaging here is the ultrasound or the CT abdomen (stone protocol).")
unavailable("ct face", "Facial CT is not in the catalog.")
unavailable("ct facial bones", "Facial CT is not in the catalog.")
unavailable("ct orbits", "Orbital CT is not in the catalog.")
unavailable("ct sinus", "Sinus CT is not in the catalog.")
unavailable("ct t spine", "Spine CT here is the C-spine; the thoracic and lumbar spine are MRI.")
unavailable("ct l spine", "Spine CT here is the C-spine; the thoracic and lumbar spine are MRI.")
unavailable("ct lumbar spine", "Spine CT here is the C-spine; the thoracic and lumbar spine are MRI.")
unavailable("ct thoracic spine", "Spine CT here is the C-spine; the thoracic and lumbar spine are MRI.")
unavailable("abdominal xr", "Plain films here are the chest and the pelvis.")
unavailable("kub", "Plain films here are the chest and the pelvis.")
unavailable("abdominal series", "Plain films here are the chest and the pelvis.")
unavailable("obstruction series", "Plain films here are the chest and the pelvis.")
unavailable("extremity xr", "Plain films here are the chest and the pelvis.")
unavailable("ankle xr", "Plain films here are the chest and the pelvis.")
unavailable("knee xr", "Plain films here are the chest and the pelvis.")
unavailable("wrist xr", "Plain films here are the chest and the pelvis.")
unavailable("shoulder xr", "Plain films here are the chest and the pelvis.")
unavailable("hand xr", "Plain films here are the chest and the pelvis.")
unavailable("foot xr", "Plain films here are the chest and the pelvis.")
unavailable("femur xr", "Plain films here are the chest and the pelvis.")
unavailable("c spine xr", "The cervical spine is imaged by CT or MRI here.")
unavailable("cervical spine xr", "The cervical spine is imaged by CT or MRI here.")
unavailable("vq scan", "V/Q is not in the catalog; the CT pulmonary embolus study is.")
unavailable("v q scan", "V/Q is not in the catalog; the CT pulmonary embolus study is.")
unavailable("ventilation perfusion scan", "V/Q is not in the catalog; the CT pulmonary embolus study is.")
unavailable("formal echo", "Only the bedside cardiac ultrasound is in the catalog.")
unavailable("tee", "Only the bedside cardiac ultrasound is in the catalog.")
unavailable("transesophageal echo", "Only the bedside cardiac ultrasound is in the catalog.")
unavailable("pelvic ultrasound", "Pelvic and transvaginal ultrasound are not in the catalog.")
unavailable("transvaginal ultrasound", "Pelvic and transvaginal ultrasound are not in the catalog.")
unavailable("tvus", "Pelvic and transvaginal ultrasound are not in the catalog.")
unavailable("ultrasound pelvis", "Pelvic and transvaginal ultrasound are not in the catalog.")
unavailable("testicular ultrasound", "Scrotal ultrasound is not in the catalog.")
unavailable("scrotal ultrasound", "Scrotal ultrasound is not in the catalog.")
unavailable("ocular ultrasound", "Ocular ultrasound is not in the catalog.")
unavailable("ultrasound eye", "Ocular ultrasound is not in the catalog.")
unavailable("bladder scan", "A bladder scanner is not in the catalog; the renal ultrasound is.")

# Stabilization. Doses, units, rates and "for the ..." trailers are stripped by the
# parser, so "a liter of normal saline for the pressure" reaches the table as
# "liter normal saline". A number is kept only where it discriminates (500 vs a liter,
# 15 liters on a mask).
alias("attach_monitor", "monitor", "attach monitor", "cardiac monitor", "on the monitor", "monitor leads", "telemetry", "tele",
      "continuous monitoring", "cardiac monitoring", "pulse ox", "pulse oximetry", "pulse oximeter", "full monitoring", "hook up the monitor",
      "hook up to the monitor", "connect the monitor", "monitors", "sat probe", "put on the monitor")
alias("insert_iv", "iv", "iv access", "peripheral iv", "large bore iv", "iv line", "peripheral line", "peripheral access", "access",
      "venous access", "18 gauge", "18 gauge iv", "16 gauge", "16 gauge iv", "20 gauge", "20 gauge iv", "large bore", "large bore access",
      "piv", "establish access", "establish iv access", "get access", "obtain access", "obtain iv access", "antecubital iv", "ac iv",
      "insert iv", "place an iv", "iv cannula", "iv catheter", "venflon", "an iv", "iv in")
alias("second_iv", "second iv", "another iv", "second line", "another line", "second access", "second peripheral iv", "second large bore",
      "second large bore iv", "one more iv", "additional iv", "additional access", "2nd iv", "2nd line", "iv number two", "iv number 2",
      "second peripheral", "other arm iv")
alias("intraosseous_line", "io", "io access", "intraosseous", "intraosseous line", "intraosseous access", "ez io", "easy io", "io line",
      "drill an io", "tibial io", "humeral io", "io needle", "place an io", "interosseous", "drill")
alias("central_venous_catheter_triple_lumen", "triple lumen", "triple lumen catheter", "triple lumen central line", "tlc",
      "central line triple lumen", "ij triple lumen", "femoral triple lumen", "subclavian triple lumen", "triple lumen cvc",
      "multi lumen catheter", "cvc triple lumen", "triple lumen line")
alias("central_venous_catheter_cordis", "cordis", "introducer", "introducer sheath", "cordis introducer", "large bore central line",
      "mac line", "mac catheter", "trauma line", "cordis line", "swan introducer", "9 french cordis", "central line cordis", "cordis central line",
      "cordis catheter", "large bore cvc", "resuscitation line")
for p in ["central line", "central access", "central venous catheter", "central venous access", "cvc", "cvl", "ij", "internal jugular",
          "femoral line", "subclavian", "subclavian line", "ij line", "femoral central line"]:
    ambiguous(p, "central_venous_catheter_triple_lumen", "central_venous_catheter_cordis")
alias("arterial_line", "arterial line", "art line", "a line", "radial arterial line", "radial art line", "femoral art line", "femoral arterial line",
      "arterial access", "arterial catheter", "invasive blood pressure", "invasive bp", "invasive blood pressure monitoring",
      "arterial pressure monitoring")
alias("nasal_cannula_oxygen", "nasal cannula", "nc", "nasal cannula oxygen", "oxygen by nasal cannula", "o2 by nasal cannula", "oxygen nasal cannula",
      "o2 nasal cannula", "2 liters", "two liters", "2 liters nasal cannula", "two liters nasal cannula", "2 liters by nasal cannula", "2 liters nc",
      "4 liters nasal cannula", "four liters nasal cannula", "4 liters nc", "6 liters nasal cannula", "six liters nasal cannula", "6 liters nc",
      "low flow oxygen", "low flow o2", "nasal prongs", "nasal o2", "nasal oxygen", "oxygen by cannula", "cannula oxygen", "4 liters", "four liters",
      "6 liters", "six liters", "2 liters oxygen", "2 liters o2", "two liters oxygen", "two liters o2", "4 liters oxygen", "4 liters o2",
      "6 liters oxygen", "6 liters o2")
alias("non_rebreather_mask", "non rebreather", "nonrebreather", "non rebreather mask", "nonrebreather mask", "nrb", "nrbm", "15 liters",
      "fifteen liters", "15 liters non rebreather", "fifteen liters non rebreather", "15 liters nrb", "15 liter nrb", "100 percent oxygen",
      "100 percent o2", "oxygen mask", "o2 mask", "reservoir mask", "max oxygen", "max o2", "full oxygen", "nrb 15", "nrb at 15", "15 l nrb",
      "nonrebreather at 15", "non rebreather at 15", "15 liters by non rebreather", "15 liters by nonrebreather", "oxygen by mask", "o2 by mask",
      "high flow oxygen by mask", "15 liters oxygen", "15 liters o2", "fifteen liters oxygen", "fifteen liters o2", "15 liters by mask",
      "100 percent nonrebreather", "100 percent non rebreather")
for p in ["oxygen", "o2", "supplemental oxygen", "supplemental o2", "some oxygen", "some o2", "titrate oxygen", "titrate o2", "put on oxygen",
          "put on o2", "oxygen therapy", "oxygen on"]:
    ambiguous(p, "nasal_cannula_oxygen", "non_rebreather_mask")
for p in ["high flow nasal cannula", "hfnc", "high flow", "high flow oxygen", "high flow o2", "heated high flow", "optiflow", "airvo", "vapotherm"]:
    unavailable(p, "High-flow nasal cannula is not in the catalog. Nasal cannula and the non-rebreather are.")
for p in ["venturi mask", "venti mask", "simple mask", "face mask", "face mask oxygen", "face mask o2"]:
    unavailable(p, "The only oxygen mask in the catalog is the non-rebreather.")
alias("non_invasive_positive_pressure_ventilation", "bipap", "bi pap", "cpap", "c pap", "niv", "nippv", "nppv", "noninvasive ventilation",
      "non invasive ventilation", "noninvasive positive pressure", "non invasive positive pressure", "noninvasive positive pressure ventilation",
      "non invasive positive pressure ventilation", "bilevel", "bi level", "bilevel positive airway pressure", "continuous positive airway pressure",
      "trial of bipap", "trial of cpap", "put on bipap", "put on cpap", "bipap trial", "cpap trial", "noninvasive", "non invasive", "bipap machine",
      "avaps", "start bipap", "start cpap", "bipap the patient", "cpap the patient", "bipap mask", "cpap mask", "niv mask", "bipap 10 over 5",
      "bipap ten over five", "bipap 12 over 6", "cpap 5", "cpap of 5", "bipap them", "cpap them")
alias("bag_valve_mask", "bag valve mask", "bvm", "bag mask", "bag the patient", "bag them", "bagging", "ambu", "ambu bag", "bag mask ventilation",
      "bag valve mask ventilation", "bvm ventilation", "assisted ventilation", "assist ventilation", "assist breathing", "ventilate with bvm",
      "bag ventilate", "manual ventilation", "two person bvm", "two person bag mask", "bvm with peep", "bag mask with peep", "start bagging",
      "bag him", "bag her", "bag valve", "self inflating bag")
ambiguous("positive pressure", "non_invasive_positive_pressure_ventilation", "bag_valve_mask")
ambiguous("positive pressure ventilation", "non_invasive_positive_pressure_ventilation", "bag_valve_mask")
ambiguous("ventilate", "bag_valve_mask", "intubate_rapid_sequence")
# Fluids. The parser canonicalises the volume and the fluid name before lookup (see CANON
# below): "a liter of normal saline", "1000 cc of NS" and "one liter sodium chloride" all
# reach the table as "liter saline", so the table lists each shape once.
SAL, LRS = ["saline"], ["lr"]
LITER = ["liter", "2 liters", "30 per kilo", "wide open", "liters", "another liter", "second liter", "liter bolus"]
HALF = ["500", "250"]
INF = ["drip", "maintenance", "kvo", "at 100", "at 125", "at 150", "at 75", "at 200", "at 250", "running", "run", "hang", "continuous"]
def fluid(cid, names, amounts):
    for n in names:
        for a in amounts:
            alias(cid, f"{a} {n}", f"{n} {a}", f"{a} {n} bolus", f"{n} {a} bolus", f"{a} bolus {n}", f"bolus {a} {n}")
fluid("normal_saline_1l_bolus", SAL, LITER)
fluid("normal_saline_500ml_bolus", SAL, HALF)
fluid("lactated_ringer_s_1l_bolus", LRS, LITER)
fluid("lactated_ringer_s_500ml_bolus", LRS, HALF)
for n in SAL:
    for t in INF: alias("normal_saline_infusion", f"{n} {t}", f"{t} {n}")
    ambiguous(n, "normal_saline_1l_bolus", "normal_saline_500ml_bolus", "normal_saline_infusion")
    ambiguous(f"{n} bolus", "normal_saline_1l_bolus", "normal_saline_500ml_bolus")
    ambiguous(f"bolus {n}", "normal_saline_1l_bolus", "normal_saline_500ml_bolus")
for n in LRS:
    for t in INF: alias("lactated_ringer_s_infusion", f"{n} {t}", f"{t} {n}")
    ambiguous(n, "lactated_ringer_s_1l_bolus", "lactated_ringer_s_500ml_bolus", "lactated_ringer_s_infusion")
    ambiguous(f"{n} bolus", "lactated_ringer_s_1l_bolus", "lactated_ringer_s_500ml_bolus")
    ambiguous(f"bolus {n}", "lactated_ringer_s_1l_bolus", "lactated_ringer_s_500ml_bolus")
for p in ["fluids", "iv fluids", "ivf", "fluid bolus", "bolus", "bolus of fluids", "crystalloid", "crystalloid bolus", "fluid", "fluid challenge",
          "iv fluid", "fluid resuscitation", "resuscitate with fluids", "volume", "volume resuscitation", "give volume"]:
    ambiguous(p, "normal_saline_1l_bolus", "lactated_ringer_s_1l_bolus", "normal_saline_500ml_bolus", "lactated_ringer_s_500ml_bolus")
for p in LITER: ambiguous(p, "normal_saline_1l_bolus", "lactated_ringer_s_1l_bolus")
for p in HALF: ambiguous(p, "normal_saline_500ml_bolus", "lactated_ringer_s_500ml_bolus")
for p in ["liter of fluid", "liter of fluids", "liter bolus of fluid", "another bolus", "repeat the bolus", "repeat bolus", "another fluid bolus",
          "repeat fluid bolus", "one more liter", "1 more liter"]:
    ambiguous(p, "normal_saline_1l_bolus", "lactated_ringer_s_1l_bolus")
for p in ["maintenance fluids", "maintenance", "maintenance ivf", "mivf", "maintenance fluid", "maintenance rate", "maintenance iv fluids"]:
    ambiguous(p, "normal_saline_infusion", "lactated_ringer_s_infusion", "d5_1_2_ns_infusion")
for p in ["plasmalyte", "plasma lyte", "hartmanns", "normosol", "isolyte", "albumin"]:
    unavailable(p, "Not in the catalog. Crystalloids available: normal saline and lactated Ringer's.")
alias("d5_1_2_ns_infusion", "d5 half normal", "d5 half normal saline", "d5 half ns", "d5 1 2 ns", "d5 half", "d five half normal",
      "d five half normal saline", "d five half", "dextrose half normal", "dextrose half normal saline", "d5 0 45", "d5 0 45 ns", "d5 point 45",
      "d5 point 45 ns", "d5 half normal with potassium", "d5 half normal saline with potassium", "d5 half ns with potassium", "d5 half normal with kcl",
      "d5 half normal saline with kcl", "d5 half ns with kcl", "dextrose containing fluids", "dextrose containing fluid", "dextrose fluids", "d5 fluids",
      "d5 containing fluids", "d5 drip", "d5 infusion", "d5 at maintenance", "d5 maintenance", "dextrose infusion", "dextrose drip", "d5w", "d5 w",
      "d 5 w", "d5w infusion", "d5w drip", "d5w at maintenance", "d10 infusion", "d10 drip", "d10 at maintenance", "d10", "d 10", "d10w", "d10w infusion",
      "d10w drip", "d10 fluids", "d5 half normal infusion", "d5 half normal saline infusion", "d5 half ns infusion", "d5 half normal drip",
      "d5 half normal saline drip", "d5 half ns drip", "d5 half normal at maintenance", "d5 half normal saline at maintenance", "d5 half ns at maintenance",
      "half normal saline", "half normal", "0 45 saline", "0 45 normal saline", "point 45 saline", "point 45 normal saline", "half normal saline infusion",
      "half normal saline drip", "half normal saline at maintenance")
alias("d5_ns_bolus", "d5 normal saline", "d5 ns", "d5 normal saline bolus", "d5 ns bolus", "d5 saline", "d5 saline bolus", "d five normal saline",
      "d five ns", "dextrose normal saline", "dextrose ns", "d5 normal", "d5 normal bolus", "d5 full normal saline", "d5 full ns", "d5 0 9", "d5 0 9 ns",
      "d5 point 9", "d5 point 9 ns", "liter of d5 normal saline", "liter of d5 ns", "liter d5 normal saline", "liter d5 ns", "d5 normal saline liter",
      "d5 ns liter", "bolus of d5 normal saline", "bolus of d5 ns", "d5 normal saline drip", "d5 ns drip", "d5 normal saline infusion", "d5 ns infusion",
      "d5 normal saline at maintenance", "d5 ns at maintenance", "d5 in normal saline", "d5 in ns", "dextrose 5 percent in normal saline",
      "dextrose 5 in normal saline", "5 percent dextrose in normal saline", "5 percent dextrose normal saline")
alias("defibrillate", "defibrillate", "defib", "defibrillation", "200 joules", "200 j", "two hundred joules",
      "120 joules", "150 joules", "360 joules", "360 j", "shock at 200", "shock at 200 joules", "shock at 360", "shock at 360 joules", "defib at 200",
      "defib 200", "defib at 360", "defib 360", "biphasic 200", "biphasic 200 joules", "max joules", "maximum joules", "max energy", "maximum energy",
      "charge to 200", "charge to 200 joules", "charge to 360", "charge to 360 joules", "charge and shock", "defibrillate at 200", "defibrillate at 360",
      "defibrillate 200", "defibrillate 360", "defibrillate the patient", "defibrillate them", "defibrillate him", "defibrillate her", "shock the vfib",
      "shock the v fib", "shock the vtach", "shock the v tach", "shock for vfib", "shock for vtach", "deliver a shock", "shock the patient", "shock them",
      "shock him", "shock her")
alias("unsynchronized_cardioversion", "unsynchronized cardioversion", "unsynced cardioversion", "unsynchronised cardioversion",
      "cardioversion unsynchronized", "cardioversion unsynced", "cardiovert unsynchronized", "cardiovert unsynced", "unsynchronized", "unsynced",
      "unsynchronised", "unsync and shock", "unsynchronized cardioversion at 200",
      "unsynced cardioversion at 200", "unsynchronized cardioversion 200", "unsynced cardioversion 200")
alias("synchronized_cardioversion", "cardiovert", "cardioversion", "synchronized cardioversion", "sync cardioversion", "synced cardioversion",
      "synchronised cardioversion", "sync and shock", "synchronize and shock", "synchronized shock", "synced shock", "sync shock", "synchronize",
      "sync", "sync on", "synchronized", "synced", "synchronised", "electrical cardioversion", "dc cardioversion", "dccv", "electricity",
      "cardiovert at 100", "cardiovert at 100 joules", "cardiovert 100", "cardiovert at 120", "cardiovert at 120 joules", "cardiovert 120",
      "cardiovert at 150", "cardiovert 150", "cardiovert at 200", "cardiovert at 200 joules", "cardiovert 200", "cardiovert at 50", "cardiovert 50",
      "sync at 100", "sync at 100 joules", "sync 100", "sync at 120", "sync at 120 joules", "sync 120", "sync at 150", "sync 150", "sync at 200",
      "sync at 200 joules", "sync 200", "sync at 50", "sync 50", "synchronized cardioversion at 100", "synchronized cardioversion at 120",
      "synchronized cardioversion at 150", "synchronized cardioversion at 200", "synchronized cardioversion at 50", "cardiovert the patient",
      "cardiovert them", "cardiovert him", "cardiovert her", "100 joules synchronized", "100 joules synced", "100 joules sync", "120 joules synchronized",
      "120 joules synced", "120 joules sync", "150 joules synchronized", "150 joules synced", "150 joules sync", "200 joules synchronized",
      "200 joules synced", "200 joules sync", "50 joules synchronized", "50 joules synced", "50 joules sync", "shock synchronized", "shock synced",
      "shock sync", "synchronized shock at 100", "synced shock at 100", "sync shock at 100", "synchronized shock at 120", "synced shock at 120",
      "sync shock at 120", "synchronized shock at 150", "synced shock at 150", "sync shock at 150", "synchronized shock at 200", "synced shock at 200",
      "sync shock at 200", "synchronized shock at 50", "synced shock at 50", "sync shock at 50", "synchronized 100", "synced 100", "synchronized 120",
      "synced 120", "synchronized 150", "synced 150", "synchronized 200", "synced 200", "synchronized 50", "synced 50", "sedate and cardiovert",
      "cardiovert with sedation", "cardioversion with sedation", "sedated cardioversion", "sync cardiovert", "synced cardiovert", "synchronized cardiovert")
for p in ["unsynced shock", "unsynchronized shock", "unsynchronised shock"]:
    ambiguous(p, "defibrillate", "unsynchronized_cardioversion")
for p in ["shock", "shock at 100", "shock at 100 joules", "shock at 120", "shock at 120 joules", "shock at 150", "shock at 150 joules", "shock at 50",
          "shock at 50 joules", "100 joules", "50 joules", "joules", "electrical therapy", "electrical"]:
    ambiguous(p, "defibrillate", "synchronized_cardioversion", "unsynchronized_cardioversion")
alias("cardiac_pacing", "pace", "pacing", "pacer", "pace the patient", "pace them", "pace him", "pace her", "transcutaneous pacing", "transcutaneous pacer",
      "tcp", "external pacing", "external pacer", "start pacing", "start the pacer", "pacing at 70", "pacing at 80", "pace at 70", "pace at 80",
      "pace at 60", "pacing at 60", "pacer at 70", "pacer at 80", "pacer at 60", "pacer on", "turn on the pacer", "pacer mode", "pacing mode",
      "demand pacing", "fixed pacing", "transvenous pacing", "transvenous pacer", "transvenous pacemaker", "tvp", "pacemaker", "temporary pacemaker",
      "temporary pacing", "temporary pacer", "cardiac pacing", "electrical pacing", "pace at 70 milliamps", "pace at 80 milliamps", "pacing at 70 milliamps",
      "pacing at 80 milliamps", "increase the milliamps", "increase milliamps", "increase pacer output", "increase pacing output", "turn up the pacer",
      "turn up pacing", "turn up the milliamps", "pace until capture", "pacer until capture", "pacing until capture", "pace to capture",
      "pace with capture", "pacing with capture", "overdrive pacing", "overdrive pace")
alias("place_pads_for_monitoring", "pads", "place pads", "pads on", "put on pads", "put pads on", "defib pads", "defibrillator pads",
      "defibrillation pads", "pacer pads", "pacing pads", "pads on the chest", "put the pads on", "place the pads", "get pads on", "apply pads",
      "apply the pads", "pads on the patient", "pads on him", "pads on her", "pads on them", "zoll pads", "lifepak pads", "multifunction pads",
      "multi function pads", "hands free pads", "electrode pads", "pad placement", "pads placed", "pads in place", "pads ready", "defib pads on",
      "defibrillator pads on", "pacer pads on", "pacing pads on", "pads for pacing", "pads for defibrillation", "pads for cardioversion",
      "pads for monitoring", "pads in case", "pads just in case", "pads on standby", "pads on and ready", "pads on the chest and back",
      "anterior posterior pads", "ap pads", "a p pads", "anterior lateral pads", "sternal apical pads", "attach pads", "attach the pads",
      "attach defib pads", "attach defibrillator pads", "attach pacer pads", "attach pacing pads", "connect pads", "connect the pads",
      "hook up pads", "hook up the pads", "pads and defibrillator", "pads and defib", "pads and pacer", "pads and zoll", "pads and lifepak",
      "defib on standby", "defibrillator on standby", "zoll on standby", "lifepak on standby", "defibrillator at bedside", "defib at bedside",
      "zoll at bedside", "lifepak at bedside", "zoll", "lifepak", "the zoll", "the lifepak")
alias("start_chest_compressions", "compressions", "chest compressions", "start compressions", "start chest compressions", "cpr", "start cpr",
      "begin cpr", "begin compressions", "begin chest compressions", "initiate cpr", "initiate compressions", "initiate chest compressions",
      "cpr in progress", "compressions in progress", "chest compressions in progress", "pump the chest", "lucas", "lucas device", "mechanical cpr",
      "mechanical compressions", "autopulse", "high quality cpr", "high quality compressions", "good compressions", "hard and fast",
      "push hard push fast", "push hard and fast", "continue cpr", "continue compressions", "continue chest compressions", "resume cpr",
      "resume compressions", "resume chest compressions", "restart cpr", "restart compressions",
      "restart chest compressions", "cardiac massage", "external cardiac massage", "closed chest massage", "bls", "start bls", "begin bls",
      "basic life support", "acls", "start acls", "begin acls", "advanced cardiac life support", "advanced cardiovascular life support",
      "cardiopulmonary resuscitation", "start cardiopulmonary resuscitation", "begin cardiopulmonary resuscitation", "two minutes of cpr",
      "two minutes of compressions", "two minutes of chest compressions", "2 minutes of cpr", "2 minutes of compressions", "2 minutes of chest compressions",
      "another round of cpr", "another round of compressions", "another round of chest compressions", "another cycle of cpr", "another cycle of compressions",
      "another cycle of chest compressions", "cycle of cpr", "cycle of compressions", "cycle of chest compressions", "round of cpr", "round of compressions",
      "round of chest compressions", "start the code", "run the code", "code the patient", "code blue", "call a code")
alias("position_for_intubation", "position for intubation", "position the patient for intubation", "sniffing position", "ear to sternal notch",
      "ramp the patient", "ramp them", "ramp him", "ramp her", "ramped position", "ramped", "ramping", "ramp", "shoulder roll", "put a shoulder roll",
      "place a shoulder roll", "towel under the shoulders", "align the airway axes", "optimize position for intubation", "optimise position for intubation",
      "position for airway", "position the patient for airway", "position for the airway", "position the patient for the airway",
      "position for laryngoscopy", "position the patient for laryngoscopy", "position for rsi", "position the patient for rsi", "sit up for intubation",
      "sit the patient up for intubation", "position for the tube", "positioning for intubation", "positioning", "position the patient", "position",
      "head of bed up for intubation", "reverse trendelenburg for intubation", "elevate the head for intubation")
alias("prepare_endotracheal_tube", "prepare the tube", "prepare endotracheal tube", "prepare et tube", "prepare ett", "prep the tube",
      "prep endotracheal tube", "prep et tube", "prep ett", "set up for intubation", "set up intubation", "set up the airway", "set up airway",
      "setup for intubation", "setup intubation", "setup the airway", "setup airway", "airway setup", "airway set up", "intubation setup",
      "intubation set up", "get the tube ready", "tube ready", "get the tube", "get a tube", "et tube", "ett", "endotracheal tube", "7 5 tube",
      "seven five tube", "7 5 et tube", "seven five et tube", "7 5 ett", "8 0 tube", "eight oh tube", "8 0 et tube", "8 0 ett", "7 0 tube",
      "seven oh tube", "7 0 et tube", "7 0 ett", "size 7 5 tube", "size 8 tube", "size 7 tube", "check the cuff", "check cuff", "test the cuff",
      "test cuff", "cuff check", "stylet", "load the stylet", "stylet in the tube", "stylet the tube", "bougie", "get a bougie", "bougie ready",
      "bougie at bedside", "get the bougie", "have a bougie ready", "laryngoscope", "get the laryngoscope", "laryngoscope ready", "laryngoscope at bedside",
      "get a laryngoscope", "check the laryngoscope", "mac 3", "mac 4", "mac three", "mac four", "miller 2", "miller 3", "miller two", "miller three",
      "mac blade", "miller blade", "glidescope", "get the glidescope", "glidescope ready", "glidescope at bedside", "video laryngoscope",
      "get the video laryngoscope", "video laryngoscope ready", "video laryngoscope at bedside", "vl", "get the vl", "vl ready", "vl at bedside",
      "c mac", "get the c mac", "c mac ready", "c mac at bedside", "airway cart", "get the airway cart", "airway cart ready", "airway cart at bedside",
      "difficult airway cart", "get the difficult airway cart", "airway box", "get the airway box", "intubation kit", "get the intubation kit",
      "intubation tray", "get the intubation tray", "airway equipment", "get the airway equipment", "airway equipment ready", "airway equipment at bedside",
      "airway supplies", "get the airway supplies", "intubation equipment", "get the intubation equipment", "intubation supplies",
      "get the intubation supplies", "co2 detector", "get the co2 detector", "colorimetric", "colorimetric co2", "end tidal ready", "end tidal co2 ready",
      "capnography ready", "backup airway", "backup airway ready", "lma ready", "lma at bedside", "get an lma", "get the lma", "lma", "igel", "i gel",
      "igel ready", "i gel ready", "get an igel", "get an i gel", "supraglottic", "supraglottic airway", "supraglottic ready", "supraglottic airway ready",
      "get a supraglottic", "sga", "sga ready", "get an sga", "prepare for intubation", "prepare intubation", "prepare the airway", "prepare airway",
      "prepare for the airway", "prepare for airway", "prepare for rsi", "prepare rsi", "prep for intubation", "prep intubation", "prep the airway",
      "prep airway", "prep for the airway", "prep for airway", "prep for rsi", "prep rsi", "get ready to intubate", "get ready for intubation",
      "get ready for the airway", "get ready for rsi", "ready to intubate", "ready for intubation", "ready for rsi", "soap me", "soapme",
      "airway checklist", "run the airway checklist", "intubation checklist", "run the intubation checklist", "rsi checklist", "run the rsi checklist",
      "ventilator ready", "vent ready", "ventilator at bedside", "vent at bedside", "get the ventilator", "get the vent", "get a ventilator",
      "get a vent", "call rt", "call respiratory", "get rt", "get respiratory", "rt to bedside", "respiratory to bedside", "rt at bedside",
      "respiratory at bedside", "respiratory therapy", "respiratory therapist", "page rt", "page respiratory", "page respiratory therapy",
      "page the respiratory therapist", "airway equipment to the bedside", "intubation equipment to the bedside")
alias("suction", "suction", "suction the airway", "suction the mouth", "suction the oropharynx", "suction the patient", "suction them", "suction him",
      "suction her", "yankauer", "yankauer suction", "yankauer ready", "get the yankauer", "get a yankauer", "suction ready", "suction at bedside",
      "suction on", "turn on suction", "turn on the suction", "set up suction", "set up the suction", "suction set up", "suction setup", "oral suction",
      "oropharyngeal suction", "suction secretions", "clear secretions", "clear the secretions", "suction the secretions", "suction out the mouth",
      "suction out the airway", "suction out the secretions", "suction the vomit", "suction the emesis", "suction out the vomit", "suction out the emesis",
      "suction the blood", "suction out the blood", "deep suction", "tracheal suction", "inline suction", "in line suction", "nasotracheal suction",
      "nasal suction", "get suction", "get the suction", "get suction ready", "get the suction ready", "wall suction", "portable suction",
      "suction catheter", "get a suction catheter", "get the suction catheter", "two suctions", "2 suctions", "double suction", "dual suction",
      "second suction", "backup suction", "back up suction", "suction times two", "suction x2", "suction x 2")
alias("preoxygenate_for_intubation", "preoxygenate", "pre oxygenate", "preoxygenation", "pre oxygenation", "preox", "pre ox",
      "preoxygenate for intubation", "pre oxygenate for intubation", "preoxygenate the patient", "pre oxygenate the patient", "preoxygenate them",
      "pre oxygenate them", "preoxygenate him", "pre oxygenate him", "preoxygenate her", "pre oxygenate her", "3 minutes of preoxygenation",
      "three minutes of preoxygenation", "3 minutes of pre oxygenation", "three minutes of pre oxygenation", "denitrogenate", "denitrogenation",
      "denitrogenate the patient", "apneic oxygenation", "apnoeic oxygenation", "apox", "ap ox", "nasal cannula for apneic oxygenation",
      "nasal cannula for apnoeic oxygenation", "flush rate nasal cannula", "flush rate oxygen", "flush rate o2", "flush rate", "nasal cannula at flush rate",
      "nasal cannula at 15", "nasal cannula at 15 liters", "nasal cannula at fifteen liters", "nc at 15", "nc at 15 liters", "nc at fifteen liters",
      "nc at flush", "nc at flush rate", "nasal cannula at flush", "nasal cannula under the mask", "nc under the mask", "nasal cannula under the nrb",
      "nc under the nrb", "nasal cannula under the non rebreather", "nc under the non rebreather", "nasal cannula under the nonrebreather",
      "nc under the nonrebreather", "nasal cannula plus non rebreather", "nc plus non rebreather", "nasal cannula plus nonrebreather",
      "nc plus nonrebreather", "nasal cannula plus nrb", "nc plus nrb", "nasal cannula and non rebreather", "nc and non rebreather",
      "nasal cannula and nonrebreather", "nc and nonrebreather", "nasal cannula and nrb", "nc and nrb", "non rebreather and nasal cannula",
      "nonrebreather and nasal cannula", "nrb and nasal cannula", "non rebreather and nc", "nonrebreather and nc", "nrb and nc",
      "non rebreather plus nasal cannula", "nonrebreather plus nasal cannula", "nrb plus nasal cannula", "non rebreather plus nc", "nonrebreather plus nc",
      "nrb plus nc", "preoxygenate with bipap", "pre oxygenate with bipap", "preoxygenate with cpap", "pre oxygenate with cpap", "preoxygenate with niv",
      "pre oxygenate with niv", "preoxygenate with bvm", "pre oxygenate with bvm", "preoxygenate with a bag", "pre oxygenate with a bag",
      "preoxygenate with the bag", "pre oxygenate with the bag", "preoxygenate with bag valve mask", "pre oxygenate with bag valve mask",
      "preoxygenate with a non rebreather", "pre oxygenate with a non rebreather", "preoxygenate with a nonrebreather", "pre oxygenate with a nonrebreather",
      "preoxygenate with an nrb", "pre oxygenate with an nrb", "preoxygenate with nrb", "pre oxygenate with nrb", "preoxygenate with non rebreather",
      "pre oxygenate with non rebreather", "preoxygenate with nonrebreather", "pre oxygenate with nonrebreather", "max preoxygenation",
      "maximal preoxygenation", "maximize preoxygenation", "maximise preoxygenation", "maximum preoxygenation", "optimize preoxygenation",
      "optimise preoxygenation", "optimal preoxygenation", "nitrogen washout", "8 vital capacity breaths", "eight vital capacity breaths",
      "vital capacity breaths", "3 minutes of tidal breathing", "three minutes of tidal breathing", "3 minutes on 100 percent",
      "three minutes on 100 percent", "3 minutes of 100 percent", "three minutes of 100 percent", "3 minutes preox", "three minutes preox",
      "3 minutes pre ox", "three minutes pre ox", "3 minutes of preox", "three minutes of preox", "3 minutes of pre ox", "three minutes of pre ox",
      "5 minutes preox", "five minutes preox", "5 minutes of preox", "five minutes of preox", "3 minutes preoxygenation", "three minutes preoxygenation",
      "5 minutes preoxygenation", "five minutes preoxygenation", "5 minutes of preoxygenation", "five minutes of preoxygenation", "preoxygenate for 3 minutes",
      "pre oxygenate for 3 minutes", "preoxygenate for three minutes", "pre oxygenate for three minutes", "ketamine assisted preoxygenation",
      "ketamine facilitated preoxygenation")
alias("intubate_rapid_sequence", "intubate", "intubation", "intubate the patient", "intubate them", "intubate him", "intubate her", "rsi",
      "rapid sequence intubation", "rapid sequence induction", "rapid sequence", "secure the airway", "definitive airway", "tube the patient",
      "tube them", "tube him", "tube her", "endotracheal intubation", "orotracheal intubation", "put in a tube", "put a tube in",
      "place an endotracheal tube", "place the endotracheal tube", "place an et tube", "place the et tube", "place the tube", "pass the tube",
      "take the airway", "manage the airway", "control the airway", "protect the airway", "we are going to intubate", "we need to intubate",
      "time to intubate", "intubate now", "intubate stat", "emergent intubation", "emergency intubation", "crash intubation", "crash airway",
      "delayed sequence intubation", "dsi", "go ahead and intubate", "proceed with intubation", "proceed to intubation", "mechanical ventilation",
      "mechanically ventilate", "put on the vent", "put on a ventilator", "put on the ventilator", "vent the patient", "laryngoscopy",
      "direct laryngoscopy", "video laryngoscopy", "definitive airway management", "airway management", "intubate with etomidate and rocuronium",
      "intubate with ketamine and rocuronium", "intubate with etomidate and succinylcholine", "intubate with ketamine and succinylcholine")
for p in ["tube", "ett", "vent", "ventilator", "the tube", "the vent", "the ventilator", "airway", "the airway"]:
    for cid in ("prepare_endotracheal_tube", "intubate_rapid_sequence"):
        A[cid] = [x for x in A[cid] if normalise(x) not in (p, "tube", "ett", "vent", "ventilator", "airway")]
    ambiguous(p, "prepare_endotracheal_tube", "intubate_rapid_sequence")
alias("cricothyrotomy", "cric", "cricothyrotomy", "cricothyroidotomy", "surgical airway", "surgical cric", "needle cric", "scalpel bougie",
      "scalpel bougie tube", "scalpel finger bougie", "cut the neck", "front of neck access", "fona", "emergency surgical airway", "cric the patient",
      "cric them", "cric him", "cric her", "cric kit", "get the cric kit", "open the cric kit", "cannot intubate cannot oxygenate",
      "cannot intubate cannot ventilate", "cico", "cicv", "quicktrach", "emergency trach", "slash trach", "surgical airway now", "cric now")
for p in ["trach", "tracheostomy"]:
    unavailable(p, "Tracheostomy is not in the catalog; the emergency surgical airway is the cricothyrotomy.")
for p in ["position", "positioning", "position the patient", "drill"]:
    for cid in list(A):
        if p in A[cid]: A[cid] = [x for x in A[cid] if x != p]

# Intubation drugs, sedation and analgesia
alias("lidocaine_bolus", "lidocaine", "lidocaine bolus", "lido", "iv lidocaine", "lidocaine push", "lidocaine pretreatment", "lidocaine pre treatment",
      "xylocaine", "lidocaine for the intubation", "lidocaine for intubation")
alias("midazolam_bolus", "midazolam", "versed", "midazolam bolus", "versed bolus", "midaz", "iv midazolam", "iv versed", "midazolam push", "versed push",
      "im midazolam", "im versed", "intranasal midazolam", "intranasal versed", "in versed", "in midazolam", "midazolam im", "versed im")
alias("etomidate_bolus", "etomidate", "etomidate bolus", "amidate", "etomidate push", "induction with etomidate", "induce with etomidate",
      "etomidate for induction", "etomidate induction", "etomidate for the intubation", "etomidate for intubation")
alias("ketamine_bolus", "ketamine bolus", "ketamine push", "ketalar", "induction with ketamine", "induce with ketamine", "ketamine for induction",
      "ketamine induction", "im ketamine", "ketamine im", "dissociative dose ketamine", "dissociate with ketamine", "dissociative dose", "ketamine dart",
      "sub dissociative ketamine", "subdissociative ketamine", "low dose ketamine", "analgesic dose ketamine", "pain dose ketamine",
      "ketamine for sedation", "ketamine sedation", "ketamine for procedural sedation", "ketamine procedural sedation", "ketamine for agitation",
      "ketamine for pain", "ketamine for analgesia", "ketamine analgesia", "ketamine for the intubation", "ketamine for intubation", "iv ketamine",
      "ketamine iv", "intranasal ketamine", "in ketamine")
alias("ketamine_infusion", "ketamine infusion", "ketamine drip", "ketamine gtt", "ketamine for sedation infusion", "ketamine sedation infusion",
      "ketamine for post intubation sedation", "ketamine post intubation sedation", "ketamine infusion for sedation", "ketamine drip for sedation",
      "ketamine infusion for pain", "ketamine drip for pain", "continuous ketamine", "ketamine continuous", "start a ketamine drip",
      "start a ketamine infusion", "start ketamine drip", "start ketamine infusion")
ambiguous("ketamine", "ketamine_bolus", "ketamine_infusion")
alias("propofol_bolus", "propofol bolus", "propofol push", "diprivan bolus", "diprivan push", "induction with propofol", "induce with propofol",
      "propofol for induction", "propofol induction", "propofol for the intubation", "propofol for intubation", "propofol for procedural sedation",
      "propofol procedural sedation", "propofol for cardioversion", "propofol for the cardioversion", "propofol for the procedure",
      "propofol for procedure", "push propofol", "push of propofol")
alias("propofol_infusion", "propofol infusion", "propofol drip", "propofol gtt", "diprivan infusion", "diprivan drip", "diprivan gtt",
      "propofol for sedation", "propofol sedation", "propofol for post intubation sedation", "propofol post intubation sedation",
      "propofol infusion for sedation", "propofol drip for sedation", "continuous propofol", "propofol continuous", "start a propofol drip",
      "start a propofol infusion", "start propofol drip", "start propofol infusion", "sedate with propofol", "propofol for the vent",
      "propofol for the ventilator", "propofol on the vent", "propofol on the ventilator")
ambiguous("propofol", "propofol_bolus", "propofol_infusion")
ambiguous("diprivan", "propofol_bolus", "propofol_infusion")
alias("succinylcholine_bolus", "succinylcholine", "sux", "succs", "succ", "suxamethonium", "anectine", "succinylcholine bolus", "sux bolus",
      "succinylcholine push", "sux push", "depolarizing paralytic", "depolarising paralytic", "depolarizing agent", "depolarising agent",
      "depolarizing neuromuscular blocker", "depolarising neuromuscular blocker", "succinylcholine for the intubation", "sux for the intubation",
      "succinylcholine for intubation", "sux for intubation", "succinylcholine for paralysis", "sux for paralysis", "paralyze with succinylcholine",
      "paralyze with sux", "paralyse with succinylcholine", "paralyse with sux")
alias("rocuronium_bolus", "rocuronium", "roc", "zemuron", "rocuronium bolus", "roc bolus", "rocuronium push", "roc push", "non depolarizing paralytic",
      "nondepolarizing paralytic", "non depolarising paralytic", "nondepolarising paralytic", "non depolarizing agent", "nondepolarizing agent",
      "non depolarizing neuromuscular blocker", "nondepolarizing neuromuscular blocker", "rock uranium", "rockuronium", "rocuroneum",
      "rocuronium for the intubation", "roc for the intubation", "rocuronium for intubation", "roc for intubation", "rocuronium for paralysis",
      "roc for paralysis", "paralyze with rocuronium", "paralyze with roc", "paralyse with rocuronium", "paralyse with roc", "rocuronium 1 2 per kilo",
      "roc 1 2 per kilo", "rocuronium 1 per kilo", "roc 1 per kilo", "rock")
for p in ["paralytic", "paralyze", "paralyse", "paralyze the patient", "paralyse the patient", "paralyze them", "paralyse them", "paralyze him",
          "paralyse him", "paralyze her", "paralyse her", "paralysis", "neuromuscular blockade", "neuromuscular blocker", "nmb", "nmba",
          "muscle relaxant", "muscle relaxation", "paralytic agent", "paralytics"]:
    ambiguous(p, "rocuronium_bolus", "succinylcholine_bolus")
for p in ["vecuronium", "vec", "cisatracurium", "nimbex", "atracurium"]:
    unavailable(p, "Not in the catalog. The paralytics available are rocuronium and succinylcholine.")
for p in ["induction agent", "induction", "induce", "induce the patient", "sedative for intubation", "sedative for the intubation", "induction dose",
          "induction med", "induction medication", "induction drug", "sedation for intubation", "sedation for the intubation"]:
    ambiguous(p, "etomidate_bolus", "ketamine_bolus", "propofol_bolus", "midazolam_bolus")
alias("phenylephrine_bolus", "phenylephrine bolus", "phenylephrine push", "push dose phenylephrine", "push dose neo", "push dose neosynephrine",
      "neo push", "neosynephrine push", "neo bolus", "neosynephrine bolus", "phenylephrine for the intubation", "phenylephrine for intubation",
      "neo for the intubation", "neo for intubation", "peri intubation phenylephrine", "peri intubation neo", "phenylephrine stick", "neo stick",
      "neo syringe", "phenylephrine syringe", "phenylephrine 100", "phenylephrine 100 mcg", "phenylephrine 100 micrograms", "neo 100",
      "neo 100 mcg", "neo 100 micrograms", "phenylephrine 200", "neo 200", "phenylephrine 50", "neo 50", "push of phenylephrine", "push of neo")
alias("phenylephrine_drip", "phenylephrine drip", "phenylephrine infusion", "phenylephrine gtt", "neo drip", "neo infusion", "neo gtt",
      "neosynephrine drip", "neosynephrine infusion", "neosynephrine gtt", "start a phenylephrine drip", "start phenylephrine drip",
      "start a neo drip", "start neo drip", "start phenylephrine", "start neo", "start neosynephrine", "phenylephrine for the pressure",
      "phenylephrine for pressure", "neo for the pressure", "neo for pressure", "phenylephrine for blood pressure", "neo for blood pressure",
      "phenylephrine for the blood pressure", "neo for the blood pressure", "phenylephrine for hypotension", "neo for hypotension",
      "phenylephrine for the hypotension", "neo for the hypotension", "phenylephrine for the map", "neo for the map", "phenylephrine for map",
      "neo for map", "phenylephrine to a map of 65", "neo to a map of 65", "phenylephrine for a map of 65", "neo for a map of 65",
      "phenylephrine titrated to map", "neo titrated to map", "titrate phenylephrine", "titrate neo", "titrate the phenylephrine", "titrate the neo",
      "hang phenylephrine", "hang neo", "hang neosynephrine", "continuous phenylephrine", "phenylephrine continuous", "phenylephrine peripheral",
      "peripheral phenylephrine", "peripheral neo", "neo peripheral", "phenylephrine peripherally", "neo peripherally")
for p in ["phenylephrine", "neo", "neosynephrine", "neo synephrine"]:
    ambiguous(p, "phenylephrine_bolus", "phenylephrine_drip")
for p in ["push dose pressor", "push dose pressors", "push dose", "peri intubation pressor", "peri intubation pressors", "pressor push",
          "pressor bolus", "push a pressor", "push some pressor"]:
    ambiguous(p, "phenylephrine_bolus", "epinephrine_bolus")
alias("fentanyl_bolus", "fentanyl", "fentanyl bolus", "fentanyl push", "iv fentanyl", "fentanyl iv", "sublimaze", "intranasal fentanyl", "in fentanyl",
      "fentanyl for pain", "fentanyl for the pain", "fentanyl for analgesia", "fentanyl for sedation", "fentanyl for the intubation",
      "fentanyl for intubation", "fentanyl pretreatment", "fentanyl pre treatment", "opioid", "opiate", "opioids", "opiates", "narcotic", "narcotics",
      "fentanyl drip", "fentanyl infusion", "fentanyl gtt")
alias("morphine_bolus", "morphine", "morphine bolus", "morphine push", "iv morphine", "morphine iv", "morphine sulfate", "morphine sulphate", "ms",
      "morphine for pain", "morphine for the pain", "morphine for analgesia", "morphine for chest pain", "morphine for the chest pain",
      "morphine for dyspnea", "morphine for the dyspnea", "morphine for air hunger", "morphine im", "im morphine", "morphine drip", "morphine infusion")
for p in ["pain medication", "pain meds", "pain med", "pain medicine", "analgesia", "analgesic", "analgesics", "something for pain",
          "something for the pain", "pain control", "control the pain", "treat the pain", "pain relief"]:
    ambiguous(p, "fentanyl_bolus", "morphine_bolus", "acetaminophen", "ibuprofen", "ketamine_bolus")
for p in ["hydromorphone", "dilaudid", "oxycodone", "percocet", "hydrocodone", "norco", "vicodin", "tramadol", "ultram", "codeine", "meperidine", "demerol",
          "oxy", "roxicodone"]:
    unavailable(p, "Not in the catalog. The opioids available are fentanyl and morphine.")
alias("lorazepam_bolus", "lorazepam", "ativan", "lorazepam bolus", "ativan bolus", "lorazepam push", "ativan push", "iv lorazepam", "iv ativan",
      "lorazepam iv", "ativan iv", "im lorazepam", "im ativan", "lorazepam im", "ativan im", "lorazepam for seizure", "ativan for seizure",
      "lorazepam for the seizure", "ativan for the seizure", "lorazepam for seizures", "ativan for seizures", "lorazepam for the seizures",
      "ativan for the seizures", "lorazepam for agitation", "ativan for agitation", "lorazepam for the agitation", "ativan for the agitation",
      "lorazepam for withdrawal", "ativan for withdrawal", "lorazepam for the withdrawal", "ativan for the withdrawal", "lorazepam for alcohol withdrawal",
      "ativan for alcohol withdrawal", "lorazepam for etoh withdrawal", "ativan for etoh withdrawal", "lorazepam for anxiety", "ativan for anxiety")
for p in ["benzo", "benzos", "benzodiazepine", "benzodiazepines", "a benzo", "some benzos", "iv benzo", "iv benzos", "benzo for seizure",
          "benzo for the seizure", "benzo for seizures", "benzo for agitation", "benzo for withdrawal", "sedative", "sedation", "sedate", "sedate the patient",
          "sedate them", "sedate him", "sedate her", "something to calm them down", "something for agitation", "something for the agitation",
          "chemical restraint", "chemical restraints", "chemical sedation", "anxiolytic", "anxiolysis"]:
    ambiguous(p, "lorazepam_bolus", "midazolam_bolus", "haloperidol", "olanzapine", "ziprasidone", "ketamine_bolus", "droperidol" if "droperidol" in IDS else "haloperidol")
for p in ["diazepam", "valium", "clonazepam", "klonopin", "chlordiazepoxide", "librium", "phenobarbital", "phenobarb", "droperidol", "inapsine",
          "dexmedetomidine", "precedex"]:
    unavailable(p, "Not in the catalog. Sedatives available: lorazepam, midazolam, ketamine, propofol, haloperidol, olanzapine, ziprasidone.")
alias("acetaminophen", "tylenol", "paracetamol", "iv acetaminophen", "iv tylenol", "ofirmev", "po acetaminophen", "po tylenol",
      "oral acetaminophen", "oral tylenol", "acetaminophen for fever", "tylenol for fever", "acetaminophen for the fever", "tylenol for the fever",
      "acetaminophen for pain", "tylenol for pain", "acetaminophen for the pain", "tylenol for the pain", "antipyretic", "antipyretics",
      "something for fever", "something for the fever", "rectal acetaminophen", "rectal tylenol", "pr acetaminophen", "pr tylenol", "tylenol suppository",
      "acetaminophen suppository", "1 gram of tylenol", "1 gram of acetaminophen", "gram of tylenol", "gram of acetaminophen", "650 of tylenol",
      "650 of acetaminophen", "1000 of tylenol", "1000 of acetaminophen")
alias("ibuprofen", "ibuprofen", "motrin", "advil", "nsaid", "nsaids", "an nsaid", "anti inflammatory", "anti inflammatories", "antiinflammatory",
      "antiinflammatories", "iv ibuprofen", "caldolor", "po ibuprofen", "oral ibuprofen", "ibuprofen for pain", "motrin for pain", "ibuprofen for the pain",
      "motrin for the pain", "ibuprofen for fever", "motrin for fever", "ibuprofen for the fever", "motrin for the fever", "600 of ibuprofen",
      "600 of motrin", "800 of ibuprofen", "800 of motrin", "400 of ibuprofen", "400 of motrin")
for p in ["ketorolac", "toradol", "naproxen", "naprosyn", "aleve", "indomethacin", "indocin", "diclofenac", "voltaren", "celecoxib", "celebrex", "meloxicam",
          "mobic"]:
    unavailable(p, "Not in the catalog. The NSAID available is ibuprofen.")
for p in ["opioid", "opiate", "opioids", "opiates", "narcotic", "narcotics"]:
    A["fentanyl_bolus"].remove(p); ambiguous(p, "fentanyl_bolus", "morphine_bolus")

# Resuscitation and vasoactive
def meds(cid, *phrases): alias(cid, *phrases)
meds("alteplase_tpa", "tpa", "t pa", "alteplase", "activase", "thrombolytics", "thrombolysis", "thrombolyse", "thrombolyze", "lytics", "lyse", "lyse the patient",
     "lytic", "lytic therapy", "systemic tpa", "systemic thrombolysis", "iv tpa", "iv alteplase", "full dose tpa", "half dose tpa", "fibrinolytics",
     "fibrinolysis", "fibrinolytic", "push tpa", "tpa bolus", "alteplase bolus", "clot buster", "clot busters", "thrombolytic", "thrombolytic therapy")
meds("tenecteplase_tnk_bolus", "tnk", "tenecteplase", "tnkase", "tnk bolus", "tenecteplase bolus", "tnk push", "tenecteplase push", "weight based tnk",
     "weight based tenecteplase")
meds("atropine_bolus", "atropine", "atropine bolus", "atropine push", "iv atropine", "im atropine", "atropine im", "atropine drip", "atropine infusion",
     "half a milligram of atropine", "atropine until secretions dry", "atropine until the secretions dry", "atropine until dry", "double the atropine",
     "double the atropine dose", "atropine 0 5", "atropine 1")
meds("epinephrine_bolus", "epinephrine bolus", "epi bolus", "epinephrine push", "epi push", "iv epinephrine", "iv epi", "epinephrine iv", "epi iv",
     "code dose epinephrine", "code dose epi", "cardiac arrest dose epinephrine", "cardiac arrest dose epi", "arrest dose epinephrine", "arrest dose epi",
     "1 to 10000 epinephrine", "1 to 10000 epi", "1 in 10000 epinephrine", "1 in 10000 epi", "one to ten thousand epinephrine", "one to ten thousand epi",
     "one in ten thousand epinephrine", "one in ten thousand epi", "epinephrine 1 to 10000", "epi 1 to 10000", "epinephrine 1 in 10000", "epi 1 in 10000",
     "another epinephrine", "another epi", "another round of epinephrine", "another round of epi", "another dose of epinephrine", "another dose of epi",
     "repeat epinephrine", "repeat epi", "repeat the epinephrine", "repeat the epi", "second epinephrine", "second epi", "second dose of epinephrine",
     "second dose of epi", "third epinephrine", "third epi", "next epinephrine", "next epi", "epinephrine is due", "epi is due", "epinephrine due", "epi due",
     "time for epinephrine", "time for epi", "epinephrine now", "epi now", "push dose epinephrine", "push dose epi", "epinephrine push dose", "epi push dose",
     "dirty epi", "dirty epinephrine", "dirty epi push", "epi stick", "epinephrine stick", "epi syringe", "epinephrine syringe", "epinephrine 1 milligram",
     "epi 1 milligram", "1 milligram of epinephrine", "1 milligram of epi", "one milligram of epinephrine", "one milligram of epi", "epinephrine 1 mg",
     "epi 1 mg", "1 of epi", "one of epi", "1 of epinephrine", "one of epinephrine", "epinephrine 1", "epi 1", "epinephrine 10 mcg", "epi 10 mcg",
     "epinephrine 20 mcg", "epi 20 mcg", "epinephrine 10", "epi 10", "epinephrine 20", "epi 20", "10 of epi", "20 of epi", "10 of epinephrine",
     "20 of epinephrine", "epi 5 to 20", "epinephrine 5 to 20", "epi 10 to 20", "epinephrine 10 to 20", "epinephrine 1 to 100000", "epi 1 to 100000",
     "epinephrine 1 in 100000", "epi 1 in 100000", "1 to 100000 epinephrine", "1 to 100000 epi", "1 in 100000 epinephrine", "1 in 100000 epi",
     "epinephrine for the arrest", "epi for the arrest", "epinephrine for arrest", "epi for arrest", "epinephrine for cardiac arrest", "epi for cardiac arrest",
     "epinephrine for pea", "epi for pea", "epinephrine for asystole", "epi for asystole", "epinephrine for vfib", "epi for vfib", "epinephrine for v fib",
     "epi for v fib", "epinephrine for vtach", "epi for vtach", "epinephrine for v tach", "epi for v tach", "epinephrine for pulseless vtach",
     "epi for pulseless vtach", "epinephrine every 3 to 5 minutes", "epi every 3 to 5 minutes", "epinephrine every three to five minutes",
     "epi every three to five minutes", "epinephrine q3 to 5", "epi q3 to 5", "epinephrine q 3 to 5", "epi q 3 to 5", "epi q3 5", "epinephrine q3 5",
     "epi every 3 minutes", "epinephrine every 3 minutes", "epi every 5 minutes", "epinephrine every 5 minutes", "epi every three minutes",
     "epinephrine every three minutes", "epi every five minutes", "epinephrine every five minutes")
meds("epinephrine_drip", "epinephrine drip", "epi drip", "epinephrine infusion", "epi infusion", "epinephrine gtt", "epi gtt", "start an epinephrine drip",
     "start an epi drip", "start epinephrine drip", "start epi drip", "start an epinephrine infusion", "start an epi infusion", "start epinephrine infusion",
     "start epi infusion", "hang epinephrine", "hang epi", "hang an epi drip", "hang an epinephrine drip", "continuous epinephrine", "continuous epi",
     "epinephrine continuous", "epi continuous", "epinephrine for the pressure", "epi for the pressure", "epinephrine for pressure", "epi for pressure",
     "epinephrine for blood pressure", "epi for blood pressure", "epinephrine for the blood pressure", "epi for the blood pressure",
     "epinephrine for hypotension", "epi for hypotension", "epinephrine for the hypotension", "epi for the hypotension", "epinephrine for shock",
     "epi for shock", "epinephrine for the shock", "epi for the shock", "epinephrine for the map", "epi for the map", "epinephrine for map", "epi for map",
     "epinephrine to a map of 65", "epi to a map of 65", "titrate epinephrine", "titrate epi", "titrate the epinephrine", "titrate the epi",
     "epinephrine titrated to map", "epi titrated to map", "epinephrine for bradycardia", "epi for bradycardia", "epinephrine for the bradycardia",
     "epi for the bradycardia", "epinephrine infusion for bradycardia", "epi infusion for bradycardia", "epinephrine drip for bradycardia",
     "epi drip for bradycardia", "epinephrine 2 to 10", "epi 2 to 10", "epinephrine 2 to 10 mcg", "epi 2 to 10 mcg", "epinephrine 2 to 10 per minute",
     "epi 2 to 10 per minute", "epinephrine at 5", "epi at 5", "epinephrine at 10", "epi at 10", "epinephrine at 0 1", "epi at 0 1", "epinephrine at 0 05",
     "epi at 0 05", "epinephrine 0 1 per kilo per minute", "epi 0 1 per kilo per minute", "epinephrine 0 05 per kilo per minute", "epi 0 05 per kilo per minute",
     "epinephrine for anaphylaxis infusion", "epi for anaphylaxis infusion", "epinephrine infusion for anaphylaxis", "epi infusion for anaphylaxis",
     "epinephrine drip for anaphylaxis", "epi drip for anaphylaxis", "epinephrine drip for refractory anaphylaxis", "epi drip for refractory anaphylaxis",
     "epinephrine infusion for refractory anaphylaxis", "epi infusion for refractory anaphylaxis", "epinephrine for refractory anaphylaxis",
     "epi for refractory anaphylaxis", "epi for the refractory anaphylaxis", "epinephrine for the refractory anaphylaxis", "epinephrine peripheral",
     "peripheral epinephrine", "peripheral epi", "epi peripheral", "epinephrine peripherally", "epi peripherally", "epi for cardiogenic shock",
     "epinephrine for cardiogenic shock", "epi for the cardiogenic shock", "epinephrine for the cardiogenic shock", "epi for septic shock",
     "epinephrine for septic shock", "epi for the septic shock", "epinephrine for the septic shock", "epi for anaphylactic shock",
     "epinephrine for anaphylactic shock", "epi for the anaphylactic shock", "epinephrine for the anaphylactic shock", "second pressor epi",
     "second pressor epinephrine", "epi as a second pressor", "epinephrine as a second pressor", "add epi", "add epinephrine", "add an epi drip",
     "add an epinephrine drip", "add epi drip", "add epinephrine drip", "add on epi", "add on epinephrine", "add on an epi drip", "add on an epinephrine drip")
meds("epinephrine_intramuscular", "im epinephrine", "im epi", "epinephrine im", "epi im", "intramuscular epinephrine", "intramuscular epi", "epinephrine intramuscular",
     "epi intramuscular", "epipen", "epi pen", "auto injector", "autoinjector", "epinephrine auto injector", "epinephrine autoinjector", "epi auto injector",
     "epi autoinjector", "0 3 of epi", "0 3 of epinephrine", "0 3 im epi", "0 3 im epinephrine", "0 3 epi im", "0 3 epinephrine im", "epi 0 3", "epinephrine 0 3",
     "epi 0 3 im", "epinephrine 0 3 im", "0 3 milligrams of epi", "0 3 milligrams of epinephrine", "0 3 mg of epi", "0 3 mg of epinephrine", "epi 0 3 mg",
     "epinephrine 0 3 mg", "epi 0 3 milligrams", "epinephrine 0 3 milligrams", "0 5 of epi im", "0 5 of epinephrine im", "0 5 im epi", "0 5 im epinephrine",
     "0 5 epi im", "0 5 epinephrine im", "epi 0 5 im", "epinephrine 0 5 im", "0 5 milligrams of epi im", "0 5 milligrams of epinephrine im", "epi 0 5 mg im",
     "epinephrine 0 5 mg im", "0 01 per kilo epi im", "0 01 per kilo epinephrine im", "epi 0 01 per kilo im", "epinephrine 0 01 per kilo im",
     "epinephrine for anaphylaxis", "epi for anaphylaxis", "epinephrine for the anaphylaxis", "epi for the anaphylaxis", "epi in the thigh",
     "epinephrine in the thigh", "epi in the lateral thigh", "epinephrine in the lateral thigh", "epi in the anterolateral thigh",
     "epinephrine in the anterolateral thigh", "epi to the thigh", "epinephrine to the thigh", "epi to the lateral thigh", "epinephrine to the lateral thigh",
     "1 to 1000 epi", "1 to 1000 epinephrine", "1 in 1000 epi", "1 in 1000 epinephrine", "one to one thousand epi", "one to one thousand epinephrine",
     "one in one thousand epi", "one in one thousand epinephrine", "epi 1 to 1000", "epinephrine 1 to 1000", "epi 1 in 1000", "epinephrine 1 in 1000",
     "epi 1 1000", "epinephrine 1 1000", "1 1000 epi", "1 1000 epinephrine", "im epi for anaphylaxis", "im epinephrine for anaphylaxis",
     "epi im for anaphylaxis", "epinephrine im for anaphylaxis", "epi im for the anaphylaxis", "epinephrine im for the anaphylaxis", "another im epi",
     "another im epinephrine", "another epi im", "another epinephrine im", "repeat im epi", "repeat im epinephrine", "repeat epi im", "repeat epinephrine im",
     "repeat the im epi", "repeat the im epinephrine", "second im epi", "second im epinephrine", "second epi im", "second epinephrine im",
     "second dose of im epi", "second dose of im epinephrine", "second dose of epi im", "second dose of epinephrine im", "epinephrine for angioedema",
     "epi for angioedema", "epinephrine for the angioedema", "epi for the angioedema", "epi for asthma", "epinephrine for asthma", "epi for the asthma",
     "epinephrine for the asthma", "im epi for asthma", "im epinephrine for asthma", "epi im for asthma", "epinephrine im for asthma",
     "im epi for the asthma", "im epinephrine for the asthma", "epi im for the asthma", "epinephrine im for the asthma", "subcutaneous epi",
     "subcutaneous epinephrine", "subq epi", "subq epinephrine", "sub q epi", "sub q epinephrine", "sq epi", "sq epinephrine", "epi subcutaneous",
     "epinephrine subcutaneous", "epi subq", "epinephrine subq", "epi sub q", "epinephrine sub q", "epi sq", "epinephrine sq", "epi shot", "epinephrine shot",
     "shot of epi", "shot of epinephrine", "a shot of epi", "a shot of epinephrine", "epi injection", "epinephrine injection", "injection of epi",
     "injection of epinephrine", "an injection of epi", "an injection of epinephrine", "epi in the leg", "epinephrine in the leg", "epi to the leg",
     "epinephrine to the leg", "epi in the arm", "epinephrine in the arm", "epi to the arm", "epinephrine to the arm", "epi in the deltoid",
     "epinephrine in the deltoid", "epi to the deltoid", "epinephrine to the deltoid", "im dose of epi", "im dose of epinephrine", "an im dose of epi",
     "an im dose of epinephrine", "intramuscular dose of epi", "intramuscular dose of epinephrine", "an intramuscular dose of epi",
     "an intramuscular dose of epinephrine")
for p in ["epinephrine", "epi", "adrenaline", "adrenalin", "some epi", "some epinephrine", "give epi", "give epinephrine", "epi please", "epinephrine please",
          "epi stat", "epinephrine stat", "epi now please", "epinephrine now please"]:
    ambiguous(p, "epinephrine_bolus", "epinephrine_drip", "epinephrine_intramuscular")
meds("vasopressin_bolus", "vasopressin bolus", "vaso bolus", "vasopressin push", "vaso push", "vasopressin 40", "vaso 40", "vasopressin 40 units",
     "vaso 40 units", "40 of vasopressin", "40 of vaso", "40 units of vasopressin", "40 units of vaso", "40 units vasopressin", "40 units vaso",
     "vasopressin for the arrest", "vaso for the arrest", "vasopressin for arrest", "vaso for arrest", "vasopressin for cardiac arrest",
     "vaso for cardiac arrest", "vasopressin for the cardiac arrest", "vaso for the cardiac arrest", "iv vasopressin", "iv vaso", "vasopressin iv",
     "vaso iv", "push vasopressin", "push vaso", "push of vasopressin", "push of vaso", "one time vasopressin", "one time vaso", "one time dose of vasopressin",
     "one time dose of vaso", "single dose vasopressin", "single dose vaso", "single dose of vasopressin", "single dose of vaso", "vasopressin 1 to 2 units",
     "vaso 1 to 2 units", "vasopressin 2 units", "vaso 2 units", "vasopressin 1 unit", "vaso 1 unit", "2 units of vasopressin", "2 units of vaso",
     "1 unit of vasopressin", "1 unit of vaso", "vasopressin 20", "vaso 20", "vasopressin 20 units", "vaso 20 units", "20 of vasopressin", "20 of vaso",
     "20 units of vasopressin", "20 units of vaso", "20 units vasopressin", "20 units vaso")
meds("vasopressin_drip", "vasopressin drip", "vaso drip", "vasopressin infusion", "vaso infusion", "vasopressin gtt", "vaso gtt", "start a vasopressin drip",
     "start a vaso drip", "start vasopressin drip", "start vaso drip", "start a vasopressin infusion", "start a vaso infusion", "start vasopressin infusion",
     "start vaso infusion", "start vasopressin", "start vaso", "hang vasopressin", "hang vaso", "hang a vasopressin drip", "hang a vaso drip",
     "continuous vasopressin", "continuous vaso", "vasopressin continuous", "vaso continuous", "vasopressin at 0 03", "vaso at 0 03", "vasopressin 0 03",
     "vaso 0 03", "vasopressin 0 03 units", "vaso 0 03 units", "vasopressin 0 03 units per minute", "vaso 0 03 units per minute", "0 03 of vasopressin",
     "0 03 of vaso", "0 03 units of vasopressin", "0 03 units of vaso", "0 03 units vasopressin", "0 03 units vaso", "vasopressin at 0 04", "vaso at 0 04",
     "vasopressin 0 04", "vaso 0 04", "vasopressin 0 04 units", "vaso 0 04 units", "vasopressin 0 04 units per minute", "vaso 0 04 units per minute",
     "0 04 of vasopressin", "0 04 of vaso", "0 04 units of vasopressin", "0 04 units of vaso", "0 04 units vasopressin", "0 04 units vaso",
     "vasopressin for the pressure", "vaso for the pressure", "vasopressin for pressure", "vaso for pressure", "vasopressin for blood pressure",
     "vaso for blood pressure", "vasopressin for the blood pressure", "vaso for the blood pressure", "vasopressin for hypotension", "vaso for hypotension",
     "vasopressin for the hypotension", "vaso for the hypotension", "vasopressin for shock", "vaso for shock", "vasopressin for the shock", "vaso for the shock",
     "vasopressin for the map", "vaso for the map", "vasopressin for map", "vaso for map", "vasopressin to a map of 65", "vaso to a map of 65",
     "vasopressin for septic shock", "vaso for septic shock", "vasopressin for the septic shock", "vaso for the septic shock", "second pressor vasopressin",
     "second pressor vaso", "vasopressin as a second pressor", "vaso as a second pressor", "add vasopressin", "add vaso", "add a vasopressin drip",
     "add a vaso drip", "add vasopressin drip", "add vaso drip", "add on vasopressin", "add on vaso", "add on a vasopressin drip", "add on a vaso drip",
     "vasopressin for vasodilatory shock", "vaso for vasodilatory shock", "vasopressin for the vasodilatory shock", "vaso for the vasodilatory shock",
     "vasopressin for distributive shock", "vaso for distributive shock", "vasopressin for the distributive shock", "vaso for the distributive shock",
     "vasopressin fixed dose", "vaso fixed dose", "fixed dose vasopressin", "fixed dose vaso", "vasopressin at a fixed dose", "vaso at a fixed dose",
     "vasopressin pitressin drip", "pitressin drip", "pitressin infusion", "pitressin", "vasostrict", "vasostrict drip", "vasostrict infusion",
     "vasopressin for gi bleed", "vaso for gi bleed", "vasopressin for the gi bleed", "vaso for the gi bleed", "vasopressin for variceal bleed",
     "vaso for variceal bleed", "vasopressin for the variceal bleed", "vaso for the variceal bleed", "vasopressin for varices", "vaso for varices",
     "vasopressin for the varices", "vaso for the varices", "vasopressin for esophageal varices", "vaso for esophageal varices",
     "vasopressin for the esophageal varices", "vaso for the esophageal varices", "vasopressin for a variceal hemorrhage", "vaso for a variceal hemorrhage",
     "vasopressin for the variceal hemorrhage", "vaso for the variceal hemorrhage", "vasopressin for variceal hemorrhage", "vaso for variceal hemorrhage",
     "vasopressin for hemorrhagic shock", "vaso for hemorrhagic shock", "vasopressin for the hemorrhagic shock", "vaso for the hemorrhagic shock",
     "vasopressin for cardiogenic shock", "vaso for cardiogenic shock", "vasopressin for the cardiogenic shock", "vaso for the cardiogenic shock",
     "vasopressin for anaphylactic shock", "vaso for anaphylactic shock", "vasopressin for the anaphylactic shock", "vaso for the anaphylactic shock",
     "vasopressin for neurogenic shock", "vaso for neurogenic shock", "vasopressin for the neurogenic shock", "vaso for the neurogenic shock",
     "vasopressin for spinal shock", "vaso for spinal shock", "vasopressin for the spinal shock", "vaso for the spinal shock", "vasopressin for obstructive shock",
     "vaso for obstructive shock", "vasopressin for the obstructive shock", "vaso for the obstructive shock", "vasopressin for refractory shock",
     "vaso for refractory shock", "vasopressin for the refractory shock", "vaso for the refractory shock", "vasopressin for refractory hypotension",
     "vaso for refractory hypotension", "vasopressin for the refractory hypotension", "vaso for the refractory hypotension")
for p in ["vasopressin", "vaso", "adh", "antidiuretic hormone", "some vasopressin", "some vaso", "give vasopressin", "give vaso"]:
    ambiguous(p, "vasopressin_bolus", "vasopressin_drip")

# The rest of the medications: names, brands, slang and route words only. The parser
# strips doses, units, rates and "for the ..." trailers before lookup, so none of those
# are written here.
DRIP = ["drip", "infusion", "gtt", "continuous", "titrate", "titrated", "peripheral"]
BOL = ["bolus", "push", "iv push", "one time", "single dose", "stat dose"]
def dripdrug(cid_drip, names, cid_bolus=None):
    for n in names:
        for t in DRIP: alias(cid_drip, f"{n} {t}", f"{t} {n}")
        if cid_bolus:
            for t in BOL: alias(cid_bolus, f"{n} {t}", f"{t} {n}")
            ambiguous(n, cid_bolus, cid_drip)
        else:
            alias(cid_drip, n)
dripdrug("norepinephrine_drip", ["norepinephrine", "norepi", "levophed", "levo", "noradrenaline", "noradrenalin", "nor epi", "levafed"])
dripdrug("dobutamine_drip", ["dobutamine", "dobuta", "dobutrex"])
dripdrug("dopamine_drip", ["dopamine", "dopa", "intropin"])
dripdrug("esmolol_drip", ["esmolol", "brevibloc"])
dripdrug("nicardipine_drip", ["nicardipine", "cardene"])
dripdrug("nitroprusside_drip", ["nitroprusside", "nipride", "sodium nitroprusside", "snp"])
dripdrug("labetalol_drip", ["labetalol", "trandate", "normodyne"], "labetalol_bolus")
alias("labetalol_bolus", "labetalol", "labetalol bolus", "labetalol push", "iv labetalol", "labetalol iv", "push labetalol")
for p in ["labetalol", "trandate", "normodyne"]: AMBIG.pop(p, None)
alias("labetalol_bolus", "trandate", "normodyne")
for p in ["pressor", "pressors", "a pressor", "start a pressor", "start pressors", "vasopressor", "vasopressors", "start a vasopressor", "start vasopressors",
          "hang a pressor", "hang pressors", "vasoactive", "vasoactives", "inotrope", "inotropes", "an inotrope", "start an inotrope", "pressor support",
          "vasopressor support", "inotropic support", "something for the pressure", "something for the blood pressure", "support the pressure",
          "support the blood pressure", "bring up the pressure", "bring up the blood pressure", "get the pressure up", "get the blood pressure up",
          "raise the pressure", "raise the blood pressure", "pressure support"]:
    ambiguous(p, "norepinephrine_drip", "epinephrine_drip", "vasopressin_drip", "phenylephrine_drip", "dopamine_drip", "dobutamine_drip")
for p in ["milrinone", "primacor", "isoproterenol", "isuprel", "angiotensin", "giapreza", "methylene blue", "hydroxocobalamin", "cyanokit"]:
    unavailable(p, "Not in the catalog. Vasoactive drips available: norepinephrine, epinephrine, vasopressin, phenylephrine, dopamine, dobutamine.")
# Nitroglycerin: three entries.
alias("nitroglycerin_drip", "nitroglycerin drip", "nitro drip", "ntg drip", "nitroglycerin infusion", "nitro infusion", "ntg infusion", "nitroglycerin gtt",
      "nitro gtt", "ntg gtt", "iv nitroglycerin", "iv nitro", "iv ntg", "nitroglycerin iv", "nitro iv", "ntg iv", "start a nitro drip", "start a nitroglycerin drip",
      "start nitro drip", "start nitroglycerin drip", "hang nitro", "hang nitroglycerin", "hang a nitro drip", "high dose nitro", "high dose nitroglycerin",
      "high dose nitro drip", "high dose nitroglycerin drip", "nitro at 50", "nitro at 100", "nitro at 200", "nitroglycerin at 50", "nitroglycerin at 100",
      "nitroglycerin at 200", "titrate nitro", "titrate nitroglycerin", "titrate the nitro", "titrate the nitroglycerin", "nitro bolus", "nitroglycerin bolus",
      "iv nitro bolus", "iv nitroglycerin bolus", "nitro push", "nitroglycerin push", "bolus of nitro", "bolus of nitroglycerin", "nitro 400 bolus",
      "nitroglycerin 400 bolus", "nitro 400 mcg bolus", "nitroglycerin 400 mcg bolus", "nitro 400 mcg", "nitroglycerin 400 mcg", "tridil", "tridil drip",
      "nitro infusion for pulmonary edema", "nitroglycerin infusion for pulmonary edema", "nitro drip for pulmonary edema", "nitroglycerin drip for pulmonary edema",
      "nitro for scape", "nitroglycerin for scape", "nitro drip for scape", "nitroglycerin drip for scape", "nitro for the scape", "nitroglycerin for the scape",
      "iv nitrates", "iv nitrate", "nitrates iv", "nitrate iv", "nitrate drip", "nitrates drip", "nitrate infusion", "nitrates infusion")
alias("nitroglycerin_sublingual", "sublingual nitroglycerin", "sublingual nitro", "sublingual ntg", "sl nitroglycerin", "sl nitro", "sl ntg",
      "nitroglycerin sublingual", "nitro sublingual", "ntg sublingual", "nitroglycerin sl", "nitro sl", "ntg sl", "nitro tab", "nitro tabs", "nitroglycerin tab",
      "nitroglycerin tabs", "ntg tab", "ntg tabs", "nitro tablet", "nitro tablets", "nitroglycerin tablet", "nitroglycerin tablets", "nitro under the tongue",
      "nitroglycerin under the tongue", "ntg under the tongue", "nitro spray", "nitroglycerin spray", "ntg spray", "nitro 0 4", "nitroglycerin 0 4",
      "ntg 0 4", "nitro 0 4 sl", "nitroglycerin 0 4 sl", "ntg 0 4 sl", "0 4 of nitro", "0 4 of nitroglycerin", "0 4 of ntg", "0 4 nitro", "0 4 nitroglycerin",
      "0 4 ntg", "0 4 sublingual nitro", "0 4 sublingual nitroglycerin", "0 4 sl nitro", "0 4 sl nitroglycerin", "400 mcg sublingual nitro",
      "400 mcg sublingual nitroglycerin", "400 mcg sl nitro", "400 mcg sl nitroglycerin", "400 micrograms sublingual nitro",
      "400 micrograms sublingual nitroglycerin", "400 micrograms sl nitro", "400 micrograms sl nitroglycerin", "nitro 400 sublingual", "nitro 400 sl",
      "nitroglycerin 400 sublingual", "nitroglycerin 400 sl", "nitrolingual", "nitrostat", "nitro q5", "nitroglycerin q5", "nitro every 5 minutes",
      "nitroglycerin every 5 minutes", "nitro every five minutes", "nitroglycerin every five minutes", "nitro q 5", "nitroglycerin q 5",
      "nitro times three", "nitroglycerin times three", "nitro x3", "nitroglycerin x3", "nitro x 3", "nitroglycerin x 3", "3 nitros", "three nitros",
      "3 nitro", "three nitro", "nitro times 3", "nitroglycerin times 3", "another nitro", "another nitroglycerin", "another sublingual nitro",
      "another sl nitro", "repeat nitro", "repeat nitroglycerin", "repeat the nitro", "repeat the nitroglycerin", "second nitro", "second nitroglycerin",
      "third nitro", "third nitroglycerin", "sublingual nitrate", "sublingual nitrates", "sl nitrate", "sl nitrates")
alias("nitroglycerin", "nitro paste", "nitroglycerin paste", "ntg paste", "nitropaste", "nitro ointment", "nitroglycerin ointment", "ntg ointment",
      "nitro patch", "nitroglycerin patch", "ntg patch", "nitro topical", "nitroglycerin topical", "ntg topical", "topical nitro", "topical nitroglycerin",
      "topical ntg", "transdermal nitro", "transdermal nitroglycerin", "transdermal ntg", "nitro on the chest", "nitroglycerin on the chest",
      "ntg on the chest", "an inch of nitro paste", "an inch of nitropaste", "inch of nitro paste", "inch of nitropaste", "1 inch of nitro paste",
      "1 inch of nitropaste", "one inch of nitro paste", "one inch of nitropaste", "2 inches of nitro paste", "2 inches of nitropaste",
      "two inches of nitro paste", "two inches of nitropaste", "half inch of nitro paste", "half inch of nitropaste", "half an inch of nitro paste",
      "half an inch of nitropaste", "nitro bid", "nitrobid", "nitro dur", "nitrodur", "minitran", "nitrol")
for p in ["nitroglycerin", "nitro", "ntg", "nitrate", "nitrates", "some nitro", "some nitroglycerin", "give nitro", "give nitroglycerin", "nitro please",
          "nitroglycerin please", "nitro stat", "nitroglycerin stat"]:
    ambiguous(p, "nitroglycerin_sublingual", "nitroglycerin_drip", "nitroglycerin")
# Cardiac
alias("adenosine_bolus", "adenosine", "adenosine bolus", "adenosine push", "adenocard", "iv adenosine", "adenosine iv", "push adenosine", "rapid push adenosine",
      "adenosine rapid push", "adenosine 6", "adenosine 12", "6 of adenosine", "12 of adenosine", "six of adenosine", "twelve of adenosine",
      "adenosine 6 milligrams", "adenosine 12 milligrams", "adenosine 6 mg", "adenosine 12 mg", "6 milligrams of adenosine", "12 milligrams of adenosine",
      "six milligrams of adenosine", "twelve milligrams of adenosine", "adenosine with a flush", "adenosine with a rapid flush", "adenosine and flush",
      "adenosine then flush", "another adenosine", "repeat adenosine", "repeat the adenosine", "second adenosine", "second dose of adenosine",
      "third adenosine", "third dose of adenosine", "adenosine again", "adenosine one more time", "one more adenosine", "adenosine number two",
      "adenosine number 2", "adenosine number three", "adenosine number 3")
alias("amiodarone_bolus_infusion", "amiodarone", "amio", "cordarone", "pacerone", "nexterone", "amiodarone bolus", "amio bolus", "amiodarone push",
      "amio push", "amiodarone infusion", "amio infusion", "amiodarone drip", "amio drip", "amiodarone gtt", "amio gtt", "amiodarone bolus and drip",
      "amio bolus and drip", "amiodarone bolus and infusion", "amio bolus and infusion", "amiodarone bolus then drip", "amio bolus then drip",
      "amiodarone bolus then infusion", "amio bolus then infusion", "amiodarone load", "amio load", "load amiodarone", "load amio",
      "load with amiodarone", "load with amio", "amiodarone loading dose", "amio loading dose", "loading dose of amiodarone", "loading dose of amio",
      "amiodarone 150", "amio 150", "amiodarone 300", "amio 300", "150 of amiodarone", "150 of amio", "300 of amiodarone", "300 of amio",
      "amiodarone 150 over 10 minutes", "amio 150 over 10 minutes", "amiodarone 150 over ten minutes", "amio 150 over ten minutes", "iv amiodarone",
      "iv amio", "amiodarone iv", "amio iv", "start amiodarone", "start amio", "start an amiodarone drip", "start an amio drip", "hang amiodarone",
      "hang amio", "amiodarone for vtach", "amio for vtach", "amiodarone for v tach", "amio for v tach", "amiodarone for vfib", "amio for vfib",
      "amiodarone for v fib", "amio for v fib", "amiodarone for afib", "amio for afib", "amiodarone for a fib", "amio for a fib", "amiodarone for the afib",
      "amio for the afib", "amiodarone for the a fib", "amio for the a fib", "amiodarone for rate control", "amio for rate control",
      "amiodarone for rhythm control", "amio for rhythm control", "amiodarone for the rhythm", "amio for the rhythm", "amiodarone for the rate",
      "amio for the rate", "another amiodarone", "another amio", "repeat amiodarone", "repeat amio", "repeat the amiodarone", "repeat the amio",
      "second amiodarone", "second amio", "second dose of amiodarone", "second dose of amio", "amiodarone again", "amio again", "amiodarone one more time",
      "amio one more time", "one more amiodarone", "one more amio", "amiodarone 1 milligram per minute", "amio 1 milligram per minute",
      "amiodarone 1 per minute", "amio 1 per minute", "amiodarone at 1", "amio at 1", "amiodarone at 1 milligram per minute", "amio at 1 milligram per minute",
      "amiodarone at 1 per minute", "amio at 1 per minute", "amiodarone at 0 5", "amio at 0 5", "amiodarone at 0 5 milligram per minute",
      "amio at 0 5 milligram per minute", "amiodarone at 0 5 per minute", "amio at 0 5 per minute", "amiodarone 0 5 per minute", "amio 0 5 per minute",
      "amiodarone 0 5 milligram per minute", "amio 0 5 milligram per minute", "antiarrhythmic", "antiarrhythmics", "an antiarrhythmic", "anti arrhythmic",
      "anti arrhythmics", "an anti arrhythmic")
alias("apixaban", "apixaban", "eliquis", "po apixaban", "po eliquis", "oral apixaban", "oral eliquis", "apixaban 5", "eliquis 5", "apixaban 10", "eliquis 10",
      "apixaban 5 milligrams", "eliquis 5 milligrams", "apixaban 10 milligrams", "eliquis 10 milligrams", "apixaban 5 mg", "eliquis 5 mg", "apixaban 10 mg",
      "eliquis 10 mg", "5 of apixaban", "5 of eliquis", "10 of apixaban", "10 of eliquis", "5 milligrams of apixaban", "5 milligrams of eliquis",
      "10 milligrams of apixaban", "10 milligrams of eliquis", "5 mg of apixaban", "5 mg of eliquis", "10 mg of apixaban", "10 mg of eliquis",
      "apixaban twice a day", "eliquis twice a day", "apixaban bid", "eliquis bid", "apixaban twice daily", "eliquis twice daily", "start apixaban",
      "start eliquis", "start on apixaban", "start on eliquis", "start the patient on apixaban", "start the patient on eliquis", "doac", "a doac",
      "noac", "a noac", "oral anticoagulant", "an oral anticoagulant", "oral anticoagulation", "start a doac", "start a noac", "start an oral anticoagulant",
      "start oral anticoagulation", "direct oral anticoagulant", "a direct oral anticoagulant", "novel oral anticoagulant", "a novel oral anticoagulant",
      "factor xa inhibitor", "a factor xa inhibitor", "xa inhibitor", "a xa inhibitor", "ten a inhibitor", "a ten a inhibitor")
for p in ["rivaroxaban", "xarelto", "dabigatran", "pradaxa", "edoxaban", "savaysa", "warfarin", "coumadin", "fondaparinux", "arixtra", "argatroban",
          "bivalirudin", "angiomax", "dalteparin", "fragmin"]:
    unavailable(p, "Not in the catalog. Anticoagulants available: heparin, enoxaparin, apixaban.")
alias("aspirin", "aspirin", "asa", "acetylsalicylic acid", "baby aspirin", "chewable aspirin", "chew aspirin", "chewed aspirin", "aspirin chewed",
      "aspirin to chew", "aspirin 325", "asa 325", "aspirin 324", "asa 324", "aspirin 81", "asa 81", "aspirin 162", "asa 162", "aspirin 300", "asa 300",
      "325 of aspirin", "325 of asa", "324 of aspirin", "324 of asa", "81 of aspirin", "81 of asa", "162 of aspirin", "162 of asa", "300 of aspirin",
      "300 of asa", "325 milligrams of aspirin", "325 milligrams of asa", "324 milligrams of aspirin", "324 milligrams of asa", "81 milligrams of aspirin",
      "81 milligrams of asa", "162 milligrams of aspirin", "162 milligrams of asa", "300 milligrams of aspirin", "300 milligrams of asa", "325 mg of aspirin",
      "325 mg of asa", "324 mg of aspirin", "324 mg of asa", "81 mg of aspirin", "81 mg of asa", "162 mg of aspirin", "162 mg of asa", "300 mg of aspirin",
      "300 mg of asa", "aspirin 325 milligrams", "asa 325 milligrams", "aspirin 324 milligrams", "asa 324 milligrams", "aspirin 81 milligrams",
      "asa 81 milligrams", "aspirin 162 milligrams", "asa 162 milligrams", "aspirin 300 milligrams", "asa 300 milligrams", "aspirin 325 mg", "asa 325 mg",
      "aspirin 324 mg", "asa 324 mg", "aspirin 81 mg", "asa 81 mg", "aspirin 162 mg", "asa 162 mg", "aspirin 300 mg", "asa 300 mg", "four baby aspirin",
      "4 baby aspirin", "four baby aspirins", "4 baby aspirins", "four 81s", "4 81s", "four 81", "4 81", "four chewable aspirin", "4 chewable aspirin",
      "four chewable aspirins", "4 chewable aspirins", "full dose aspirin", "full strength aspirin", "adult aspirin", "an aspirin", "some aspirin",
      "give aspirin", "give asa", "aspirin please", "asa please", "aspirin stat", "asa stat", "aspirin now", "asa now", "aspirin po", "asa po", "po aspirin",
      "po asa", "oral aspirin", "oral asa", "aspirin by mouth", "asa by mouth", "aspirin pr", "asa pr", "pr aspirin", "pr asa", "rectal aspirin", "rectal asa",
      "aspirin suppository", "asa suppository", "aspirin per rectum", "asa per rectum", "ecotrin", "bayer", "bufferin", "antiplatelet", "antiplatelets",
      "an antiplatelet", "antiplatelet therapy", "antiplatelet agent", "an antiplatelet agent")
alias("atorvastatin", "atorvastatin", "lipitor", "statin", "a statin", "high intensity statin", "high dose statin", "atorvastatin 80", "lipitor 80",
      "atorvastatin 40", "lipitor 40", "80 of atorvastatin", "80 of lipitor", "40 of atorvastatin", "40 of lipitor", "atorvastatin 80 milligrams",
      "lipitor 80 milligrams", "atorvastatin 40 milligrams", "lipitor 40 milligrams", "atorvastatin 80 mg", "lipitor 80 mg", "atorvastatin 40 mg",
      "lipitor 40 mg", "80 milligrams of atorvastatin", "80 milligrams of lipitor", "40 milligrams of atorvastatin", "40 milligrams of lipitor",
      "80 mg of atorvastatin", "80 mg of lipitor", "40 mg of atorvastatin", "40 mg of lipitor", "start a statin", "start atorvastatin", "start lipitor",
      "start on a statin", "start on atorvastatin", "start on lipitor", "start the patient on a statin", "start the patient on atorvastatin",
      "start the patient on lipitor", "statin therapy", "high intensity statin therapy", "high dose statin therapy", "po atorvastatin", "po lipitor",
      "oral atorvastatin", "oral lipitor", "atorvastatin po", "lipitor po", "atorvastatin by mouth", "lipitor by mouth")
for p in ["rosuvastatin", "crestor", "simvastatin", "zocor", "pravastatin", "pravachol", "lovastatin", "mevacor"]:
    unavailable(p, "Not in the catalog. The statin available is atorvastatin.")
alias("clopidogrel", "clopidogrel", "plavix", "clopidogrel load", "plavix load", "load clopidogrel", "load plavix", "load with clopidogrel", "load with plavix",
      "clopidogrel loading dose", "plavix loading dose", "loading dose of clopidogrel", "loading dose of plavix", "clopidogrel 600", "plavix 600",
      "clopidogrel 300", "plavix 300", "clopidogrel 75", "plavix 75", "600 of clopidogrel", "600 of plavix", "300 of clopidogrel", "300 of plavix",
      "75 of clopidogrel", "75 of plavix", "clopidogrel 600 milligrams", "plavix 600 milligrams", "clopidogrel 300 milligrams", "plavix 300 milligrams",
      "clopidogrel 75 milligrams", "plavix 75 milligrams", "clopidogrel 600 mg", "plavix 600 mg", "clopidogrel 300 mg", "plavix 300 mg", "clopidogrel 75 mg",
      "plavix 75 mg", "600 milligrams of clopidogrel", "600 milligrams of plavix", "300 milligrams of clopidogrel", "300 milligrams of plavix",
      "75 milligrams of clopidogrel", "75 milligrams of plavix", "600 mg of clopidogrel", "600 mg of plavix", "300 mg of clopidogrel", "300 mg of plavix",
      "75 mg of clopidogrel", "75 mg of plavix", "p2y12", "p2y12 inhibitor", "a p2y12 inhibitor", "p2y12 inhibitor load", "p2y12 load", "load a p2y12",
      "load a p2y12 inhibitor", "p2y12 loading dose", "p2y12 inhibitor loading dose", "second antiplatelet", "a second antiplatelet",
      "second antiplatelet agent", "a second antiplatelet agent", "po clopidogrel", "po plavix", "oral clopidogrel", "oral plavix", "clopidogrel po",
      "plavix po", "clopidogrel by mouth", "plavix by mouth", "start clopidogrel", "start plavix", "start on clopidogrel", "start on plavix",
      "start the patient on clopidogrel", "start the patient on plavix", "give clopidogrel", "give plavix", "clopidogrel please", "plavix please",
      "clopidogrel stat", "plavix stat", "clopidogrel now", "plavix now")
for p in ["ticagrelor", "brilinta", "prasugrel", "effient", "cangrelor", "kengreal", "eptifibatide", "integrilin", "tirofiban", "aggrastat", "abciximab", "reopro",
          "gp 2b 3a", "gp iib iiia", "2b 3a inhibitor", "iib iiia inhibitor"]:
    unavailable(p, "Not in the catalog. Antiplatelets available: aspirin, clopidogrel.")
alias("digoxin_bolus", "digoxin", "dig", "lanoxin", "digoxin bolus", "dig bolus", "digoxin push", "dig push", "iv digoxin", "iv dig", "digoxin iv", "dig iv",
      "digoxin load", "dig load", "load digoxin", "load dig", "load with digoxin", "load with dig", "digoxin loading dose", "dig loading dose",
      "loading dose of digoxin", "loading dose of dig", "digitalize", "digitalise", "digitalization", "digitalisation", "digoxin 0 5", "dig 0 5",
      "digoxin 0 25", "dig 0 25", "0 5 of digoxin", "0 5 of dig", "0 25 of digoxin", "0 25 of dig", "digoxin 0 5 milligrams", "dig 0 5 milligrams",
      "digoxin 0 25 milligrams", "dig 0 25 milligrams", "digoxin 0 5 mg", "dig 0 5 mg", "digoxin 0 25 mg", "dig 0 25 mg", "0 5 milligrams of digoxin",
      "0 5 milligrams of dig", "0 25 milligrams of digoxin", "0 25 milligrams of dig", "0 5 mg of digoxin", "0 5 mg of dig", "0 25 mg of digoxin",
      "0 25 mg of dig", "digoxin 500", "dig 500", "digoxin 250", "dig 250", "500 of digoxin", "500 of dig", "250 of digoxin", "250 of dig", "digoxin 500 mcg",
      "dig 500 mcg", "digoxin 250 mcg", "dig 250 mcg", "digoxin 500 micrograms", "dig 500 micrograms", "digoxin 250 micrograms", "dig 250 micrograms",
      "500 mcg of digoxin", "500 mcg of dig", "250 mcg of digoxin", "250 mcg of dig", "500 micrograms of digoxin", "500 micrograms of dig",
      "250 micrograms of digoxin", "250 micrograms of dig", "digoxin for rate control", "dig for rate control", "digoxin for the rate", "dig for the rate",
      "digoxin for afib", "dig for afib", "digoxin for a fib", "dig for a fib", "digoxin for the afib", "dig for the afib", "digoxin for the a fib",
      "dig for the a fib", "digoxin for heart failure", "dig for heart failure", "digoxin for the heart failure", "dig for the heart failure",
      "digoxin for chf", "dig for chf", "digoxin for the chf", "dig for the chf", "give digoxin", "give dig", "digoxin please", "dig please", "digoxin stat",
      "dig stat", "digoxin now", "dig now", "start digoxin", "start dig", "start on digoxin", "start on dig", "start the patient on digoxin",
      "start the patient on dig", "po digoxin", "po dig", "oral digoxin", "oral dig", "digoxin po", "dig po", "digoxin by mouth", "dig by mouth")
alias("diltiazem_bolus", "diltiazem", "cardizem", "dilt", "diltiazem bolus", "cardizem bolus", "dilt bolus", "diltiazem push", "cardizem push", "dilt push",
      "iv diltiazem", "iv cardizem", "iv dilt", "diltiazem iv", "cardizem iv", "dilt iv", "diltiazem drip", "cardizem drip", "dilt drip", "diltiazem infusion",
      "cardizem infusion", "dilt infusion", "diltiazem gtt", "cardizem gtt", "dilt gtt", "diltiazem bolus and drip", "cardizem bolus and drip",
      "dilt bolus and drip", "diltiazem bolus then drip", "cardizem bolus then drip", "dilt bolus then drip", "diltiazem 0 25 per kilo",
      "cardizem 0 25 per kilo", "dilt 0 25 per kilo", "diltiazem 0 35 per kilo", "cardizem 0 35 per kilo", "dilt 0 35 per kilo", "0 25 per kilo diltiazem",
      "0 25 per kilo cardizem", "0 25 per kilo dilt", "0 35 per kilo diltiazem", "0 35 per kilo cardizem", "0 35 per kilo dilt", "diltiazem 10", "cardizem 10",
      "dilt 10", "diltiazem 20", "cardizem 20", "dilt 20", "diltiazem 15", "cardizem 15", "dilt 15", "diltiazem 25", "cardizem 25", "dilt 25", "10 of diltiazem",
      "10 of cardizem", "10 of dilt", "20 of diltiazem", "20 of cardizem", "20 of dilt", "15 of diltiazem", "15 of cardizem", "15 of dilt", "25 of diltiazem",
      "25 of cardizem", "25 of dilt", "diltiazem 10 milligrams", "cardizem 10 milligrams", "dilt 10 milligrams", "diltiazem 20 milligrams",
      "cardizem 20 milligrams", "dilt 20 milligrams", "diltiazem 15 milligrams", "cardizem 15 milligrams", "dilt 15 milligrams", "diltiazem 25 milligrams",
      "cardizem 25 milligrams", "dilt 25 milligrams", "diltiazem 10 mg", "cardizem 10 mg", "dilt 10 mg", "diltiazem 20 mg", "cardizem 20 mg", "dilt 20 mg",
      "diltiazem 15 mg", "cardizem 15 mg", "dilt 15 mg", "diltiazem 25 mg", "cardizem 25 mg", "dilt 25 mg", "10 milligrams of diltiazem",
      "10 milligrams of cardizem", "10 milligrams of dilt", "20 milligrams of diltiazem", "20 milligrams of cardizem", "20 milligrams of dilt",
      "15 milligrams of diltiazem", "15 milligrams of cardizem", "15 milligrams of dilt", "25 milligrams of diltiazem", "25 milligrams of cardizem",
      "25 milligrams of dilt", "10 mg of diltiazem", "10 mg of cardizem", "10 mg of dilt", "20 mg of diltiazem", "20 mg of cardizem", "20 mg of dilt",
      "15 mg of diltiazem", "15 mg of cardizem", "15 mg of dilt", "25 mg of diltiazem", "25 mg of cardizem", "25 mg of dilt", "diltiazem for rate control",
      "cardizem for rate control", "dilt for rate control", "diltiazem for the rate", "cardizem for the rate", "dilt for the rate", "diltiazem for afib",
      "cardizem for afib", "dilt for afib", "diltiazem for a fib", "cardizem for a fib", "dilt for a fib", "diltiazem for the afib", "cardizem for the afib",
      "dilt for the afib", "diltiazem for the a fib", "cardizem for the a fib", "dilt for the a fib", "diltiazem for svt", "cardizem for svt", "dilt for svt",
      "diltiazem for the svt", "cardizem for the svt", "dilt for the svt", "diltiazem for aflutter", "cardizem for aflutter", "dilt for aflutter",
      "diltiazem for a flutter", "cardizem for a flutter", "dilt for a flutter", "diltiazem for the flutter", "cardizem for the flutter", "dilt for the flutter",
      "another diltiazem", "another cardizem", "another dilt", "repeat diltiazem", "repeat cardizem", "repeat dilt", "repeat the diltiazem",
      "repeat the cardizem", "repeat the dilt", "second diltiazem", "second cardizem", "second dilt", "second dose of diltiazem", "second dose of cardizem",
      "second dose of dilt", "diltiazem again", "cardizem again", "dilt again", "diltiazem one more time", "cardizem one more time", "dilt one more time",
      "one more diltiazem", "one more cardizem", "one more dilt", "give diltiazem", "give cardizem", "give dilt", "diltiazem please", "cardizem please",
      "dilt please", "diltiazem stat", "cardizem stat", "dilt stat", "diltiazem now", "cardizem now", "dilt now", "start diltiazem", "start cardizem",
      "start dilt", "start a diltiazem drip", "start a cardizem drip", "start a dilt drip", "hang diltiazem", "hang cardizem", "hang dilt",
      "hang a diltiazem drip", "hang a cardizem drip", "hang a dilt drip", "calcium channel blocker", "a calcium channel blocker", "ccb", "a ccb",
      "non dihydropyridine", "a non dihydropyridine", "non dihydropyridine calcium channel blocker", "a non dihydropyridine calcium channel blocker")
for p in ["verapamil", "calan", "isoptin", "amlodipine", "norvasc", "nifedipine", "procardia", "adalat", "clevidipine", "cleviprex"]:
    unavailable(p, "Not in the catalog. Calcium channel blockers available: diltiazem, nicardipine.")
alias("enoxaparin", "enoxaparin", "lovenox", "low molecular weight heparin", "lmwh", "subq enoxaparin", "subq lovenox", "sub q enoxaparin", "sub q lovenox",
      "subcutaneous enoxaparin", "subcutaneous lovenox", "enoxaparin 1 per kilo", "lovenox 1 per kilo", "therapeutic enoxaparin", "therapeutic lovenox",
      "treatment dose enoxaparin", "treatment dose lovenox", "full dose enoxaparin", "full dose lovenox", "prophylactic enoxaparin", "prophylactic lovenox",
      "enoxaparin 40", "lovenox 40", "dvt prophylaxis", "vte prophylaxis", "chemical dvt prophylaxis", "chemoprophylaxis", "clexane")
alias("heparin_bolus_drip", "heparin", "heparin bolus", "heparin drip", "heparin infusion", "heparin gtt", "heparin bolus and drip", "heparin bolus then drip",
      "heparin bolus and infusion", "iv heparin", "heparin iv", "unfractionated heparin", "ufh", "heparin load", "load heparin", "load with heparin",
      "heparin 80 per kilo", "heparin 60 per kilo", "heparin 5000", "heparin 4000", "5000 of heparin", "4000 of heparin", "5000 units of heparin",
      "4000 units of heparin", "start heparin", "start a heparin drip", "hang heparin", "hang a heparin drip", "heparinize", "heparinise",
      "full dose heparin", "therapeutic heparin", "weight based heparin", "heparin nomogram", "heparin per protocol", "heparin protocol",
      "acs heparin", "acs dose heparin", "pe dose heparin", "subq heparin", "subcutaneous heparin", "heparin 5000 subq", "heparin 5000 sq",
      "systemic anticoagulation", "anticoagulate", "anticoagulation", "anticoagulate the patient", "start anticoagulation", "therapeutic anticoagulation",
      "full anticoagulation", "iv anticoagulation")
ambiguous("anticoagulant", "heparin_bolus_drip", "enoxaparin", "apixaban")
ambiguous("an anticoagulant", "heparin_bolus_drip", "enoxaparin", "apixaban")
ambiguous("blood thinner", "heparin_bolus_drip", "enoxaparin", "apixaban")
ambiguous("blood thinners", "heparin_bolus_drip", "enoxaparin", "apixaban")
alias("magnesium_sulfate", "magnesium sulfate", "mag sulfate", "magnesium sulfate drip", "magnesium sulfate infusion", "magnesium sulfate gtt", "magnesium sulfate rate", "magnesium sulfate at 2 an hour", "magnesium sulfate at 1 an hour", "magnesium sulphate", "mag sulphate", "mgso4", "mg so4", "iv magnesium", "iv mag", "magnesium iv",
      "mag iv", "magnesium drip", "mag drip", "magnesium infusion", "mag infusion", "magnesium gtt", "mag gtt", "2 grams of magnesium", "2 grams of mag",
      "two grams of magnesium", "two grams of mag", "2 of magnesium", "2 of mag", "two of magnesium", "two of mag", "magnesium 2 grams", "mag 2 grams",
      "magnesium 2", "mag 2", "4 grams of magnesium", "4 grams of mag", "four grams of magnesium", "four grams of mag", "magnesium 4 grams", "mag 4 grams",
      "magnesium 4", "mag 4", "6 grams of magnesium", "6 grams of mag", "magnesium 6 grams", "mag 6 grams", "1 gram of magnesium", "1 gram of mag",
      "gram of magnesium", "gram of mag", "magnesium 1 gram", "mag 1 gram", "magnesium bolus", "mag bolus", "magnesium push", "mag push", "replete magnesium",
      "replete mag", "replete the magnesium", "replete the mag", "magnesium repletion", "mag repletion", "give magnesium", "give mag", "magnesium for torsades",
      "mag for torsades", "magnesium for the torsades", "mag for the torsades", "magnesium for asthma", "mag for asthma", "magnesium for the asthma",
      "mag for the asthma", "magnesium for eclampsia", "mag for eclampsia", "magnesium for the eclampsia", "mag for the eclampsia", "magnesium for preeclampsia",
      "mag for preeclampsia", "magnesium for pre eclampsia", "mag for pre eclampsia", "magnesium for seizure prophylaxis", "mag for seizure prophylaxis",
      "magnesium load", "mag load", "load magnesium", "load mag", "load with magnesium", "load with mag", "magnesium loading dose", "mag loading dose",
      "loading dose of magnesium", "loading dose of mag", "magnesium 4 grams then 2 an hour", "mag 4 grams then 2 an hour", "magnesium 4 then 2",
      "mag 4 then 2", "magnesium 6 grams then 2 an hour", "mag 6 grams then 2 an hour", "magnesium 6 then 2", "mag 6 then 2", "magnesium at 2 an hour",
      "mag at 2 an hour", "magnesium 2 an hour", "mag 2 an hour", "magnesium 2 grams an hour", "mag 2 grams an hour", "magnesium 2 grams per hour",
      "mag 2 grams per hour", "magnesium at 1 an hour", "mag at 1 an hour", "magnesium 1 an hour", "mag 1 an hour", "magnesium 1 gram an hour",
      "mag 1 gram an hour", "magnesium 1 gram per hour", "mag 1 gram per hour", "start magnesium", "start mag", "start a magnesium drip", "start a mag drip",
      "hang magnesium", "hang mag", "hang a magnesium drip", "hang a mag drip", "magnesium over 10 minutes", "mag over 10 minutes",
      "magnesium over ten minutes", "mag over ten minutes", "magnesium over 20 minutes", "mag over 20 minutes", "magnesium over twenty minutes",
      "mag over twenty minutes", "magnesium over 15 minutes", "mag over 15 minutes", "magnesium over fifteen minutes", "mag over fifteen minutes",
      "magnesium over 5 minutes", "mag over 5 minutes", "magnesium over five minutes", "mag over five minutes", "magnesium over 2 minutes",
      "mag over 2 minutes", "magnesium over two minutes", "mag over two minutes", "magnesium over 1 minute", "mag over 1 minute", "magnesium over one minute",
      "mag over one minute", "magnesium wide open", "mag wide open", "magnesium fast", "mag fast", "fast magnesium", "fast mag", "magnesium rapid",
      "mag rapid", "rapid magnesium", "rapid mag", "magnesium slow", "mag slow", "slow magnesium", "slow mag", "magnesium slowly", "mag slowly",
      "slowly magnesium", "slowly mag", "epsom salt", "epsom salts")
for p in ["magnesium", "mag", "mg", "some magnesium", "some mag", "magnesium please", "mag please", "magnesium stat", "mag stat", "magnesium now", "mag now"]:
    ambiguous(p, "magnesium_sulfate", "magnesium_level")
# Two magnesium sulfate entries: the bolus aliases move to the bolus entry, the rest stay.
A["magnesium_sulfate_bolus"] = [p for p in A["magnesium_sulfate"] if "bolus" in p or "push" in p] + ["magnesium sulfate bolus", "magnesium sulfate push", "mag sulfate bolus", "mag sulfate push"]
A["magnesium_sulfate"] = [p for p in A["magnesium_sulfate"] if p not in A["magnesium_sulfate_bolus"]]
# The bare nitroglycerin entry is not the paste; nothing here asserts a route for it.
A["nitroglycerin"] = []
for p in ["nitro paste", "nitroglycerin paste", "nitropaste", "nitro ointment", "nitro patch", "nitroglycerin patch", "topical nitro", "topical nitroglycerin",
          "transdermal nitroglycerin", "nitro bid", "nitrobid", "nitro dur", "nitrodur"]:
    unavailable(p, "Topical nitroglycerin is not in the catalog. Sublingual and the drip are.")

alias("metoprolol_bolus", "metoprolol", "lopressor", "metoprolol bolus", "lopressor bolus", "metoprolol push", "lopressor push", "iv metoprolol", "iv lopressor",
      "metoprolol tartrate", "toprol", "beta blocker", "a beta blocker", "beta blockade", "beta blockers", "iv beta blocker")
for p in ["beta blocker", "a beta blocker", "beta blockade", "beta blockers", "iv beta blocker"]:
    A["metoprolol_bolus"].remove(p); ambiguous(p, "metoprolol_bolus", "esmolol_drip", "labetalol_bolus", "labetalol_drip", "propranolol_bolus")
alias("propranolol_bolus", "propranolol", "inderal", "propranolol bolus", "inderal bolus", "iv propranolol", "propranolol push")
for p in ["atenolol", "tenormin", "carvedilol", "coreg", "bisoprolol", "nebivolol", "sotalol"]:
    unavailable(p, "Not in the catalog. Beta blockers available: metoprolol, esmolol, labetalol, propranolol.")
alias("procainamide_drip", "procainamide", "pronestyl", "procainamide drip", "procainamide infusion", "procainamide gtt", "procainamide bolus", "procainamide load",
      "iv procainamide", "procan")
for p in ["lidocaine drip", "lidocaine infusion", "lidocaine gtt", "ibutilide", "corvert", "flecainide", "propafenone", "sotalol", "dofetilide", "tikosyn"]:
    unavailable(p, "Not in the catalog. Antiarrhythmics available: amiodarone, procainamide, lidocaine bolus, adenosine.")
for p in ["rate control", "rate control agent", "something for rate control", "control the rate", "slow the rate", "slow down the rate", "slow the heart rate",
          "av nodal blocker", "av nodal blockade", "nodal agent", "nodal blocker"]:
    ambiguous(p, "diltiazem_bolus", "metoprolol_bolus", "esmolol_drip", "digoxin_bolus", "amiodarone_bolus_infusion")
# Respiratory
alias("albuterol", "albuterol", "salbutamol", "ventolin", "proventil", "proair", "albuterol neb", "albuterol nebulizer", "albuterol nebuliser", "albuterol nebs",
      "neb", "nebs", "nebulizer", "nebuliser", "nebulizer treatment", "nebuliser treatment", "breathing treatment", "breathing treatments", "bronchodilator",
      "bronchodilators", "beta agonist", "a beta agonist", "beta 2 agonist", "saba", "continuous albuterol", "continuous nebs", "continuous neb",
      "albuterol continuous", "stacked nebs", "stacked albuterol", "back to back nebs", "back to back albuterol", "albuterol mdi", "albuterol inhaler",
      "inhaler", "puffs of albuterol", "albuterol puffs", "albuterol 2 5", "albuterol 5", "albuterol 10", "albuterol 15", "albuterol 20", "2 5 of albuterol",
      "5 of albuterol", "10 of albuterol", "15 of albuterol", "20 of albuterol", "albuterol nebs back to back", "hourly albuterol", "albuterol every 20 minutes",
      "albuterol q20", "albuterol times three", "albuterol x3", "albuterol x 3", "3 albuterol nebs", "three albuterol nebs", "xopenex", "levalbuterol",
      "albuterol via nebulizer", "albuterol via neb", "albuterol by neb", "albuterol by nebulizer", "albuterol treatment", "albuterol treatments",
      "nebulized albuterol", "nebulised albuterol", "albuterol in line", "inline albuterol", "in line albuterol", "albuterol through the vent",
      "albuterol through the bipap", "albuterol via bipap", "albuterol with the bipap", "albuterol in the bipap", "neb in the bipap", "neb through the bipap",
      "neb via bipap", "nebs through the bipap", "nebs via bipap", "nebs in the bipap")
alias("ipratropium", "ipratropium", "atrovent", "ipratropium bromide", "ipratropium neb", "atrovent neb", "ipratropium nebulizer", "atrovent nebulizer",
      "ipratropium nebs", "atrovent nebs", "anticholinergic neb", "anticholinergic nebs", "ipratropium 0 5", "atrovent 0 5", "0 5 of ipratropium",
      "0 5 of atrovent", "ipratropium 500", "atrovent 500", "500 of ipratropium", "500 of atrovent", "ipratropium 500 mcg", "atrovent 500 mcg",
      "ipratropium 500 micrograms", "atrovent 500 micrograms", "nebulized ipratropium", "nebulised ipratropium", "nebulized atrovent", "nebulised atrovent")
for p in ["terbutaline", "brethine", "aminophylline", "theophylline", "heliox", "racemic epi", "racemic epinephrine", "nebulized epi", "nebulized epinephrine",
          "nebulised epi", "nebulised epinephrine", "epi neb", "epinephrine neb", "budesonide neb", "pulmicort", "tiotropium", "spiriva"]:
    unavailable(p, "Not in the catalog. Respiratory medications available: albuterol, ipratropium, magnesium sulfate, steroids.")
# Steroids
alias("methylprednisolone_bolus", "methylprednisolone", "solumedrol", "solu medrol", "methylpred", "methylprednisolone bolus", "solumedrol bolus", "iv methylprednisolone",
      "iv solumedrol", "methylprednisolone push", "solumedrol push", "medrol", "iv steroids", "iv steroid", "high dose steroids", "high dose steroid",
      "pulse dose steroids", "pulse steroids", "125 of solumedrol", "125 of methylprednisolone", "solumedrol 125", "methylprednisolone 125", "80 of solumedrol",
      "80 of methylprednisolone", "solumedrol 80", "methylprednisolone 80", "60 of solumedrol", "60 of methylprednisolone", "solumedrol 60",
      "methylprednisolone 60", "40 of solumedrol", "40 of methylprednisolone", "solumedrol 40", "methylprednisolone 40", "a gram of solumedrol",
      "gram of solumedrol", "1 gram of solumedrol", "solumedrol 1 gram", "methylprednisolone 1 gram", "gram of methylprednisolone")
alias("dexamethasone", "dexamethasone", "decadron", "dex", "iv dexamethasone", "iv decadron", "iv dex", "dexamethasone bolus", "decadron bolus", "dex bolus",
      "dexamethasone push", "decadron push", "dex push", "po dexamethasone", "po decadron", "po dex", "oral dexamethasone", "oral decadron", "oral dex",
      "im dexamethasone", "im decadron", "im dex", "dexamethasone 10", "decadron 10", "dex 10", "10 of dexamethasone", "10 of decadron", "10 of dex",
      "dexamethasone 4", "decadron 4", "dex 4", "4 of dexamethasone", "4 of decadron", "4 of dex", "dexamethasone 6", "decadron 6", "dex 6", "6 of dexamethasone",
      "6 of decadron", "6 of dex", "dexamethasone 8", "decadron 8", "dex 8", "8 of dexamethasone", "8 of decadron", "8 of dex", "dexamethasone 0 6 per kilo",
      "decadron 0 6 per kilo", "dex 0 6 per kilo", "0 6 per kilo dexamethasone", "0 6 per kilo decadron", "0 6 per kilo dex", "dexamethasone 16",
      "decadron 16", "dex 16", "16 of dexamethasone", "16 of decadron", "16 of dex", "dexamethasone 20", "decadron 20", "dex 20", "20 of dexamethasone",
      "20 of decadron", "20 of dex", "dexamethasone 40", "decadron 40", "dex 40", "40 of dexamethasone", "40 of decadron", "40 of dex",
      "dexamethasone for croup", "decadron for croup", "dex for croup", "dexamethasone for meningitis", "decadron for meningitis", "dex for meningitis",
      "dexamethasone before antibiotics", "decadron before antibiotics", "dex before antibiotics", "dexamethasone with the first dose of antibiotics",
      "decadron with the first dose of antibiotics", "dex with the first dose of antibiotics", "dexamethasone for asthma", "decadron for asthma",
      "dex for asthma", "dexamethasone for copd", "decadron for copd", "dex for copd", "dexamethasone for the asthma", "decadron for the asthma",
      "dex for the asthma", "dexamethasone for the copd", "decadron for the copd", "dex for the copd", "dexamethasone for cerebral edema",
      "decadron for cerebral edema", "dex for cerebral edema", "dexamethasone for the cerebral edema", "decadron for the cerebral edema",
      "dex for the cerebral edema", "dexamethasone for vasogenic edema", "decadron for vasogenic edema", "dex for vasogenic edema",
      "dexamethasone for cord compression", "decadron for cord compression", "dex for cord compression", "dexamethasone for the cord compression",
      "decadron for the cord compression", "dex for the cord compression", "dexamethasone for spinal cord compression", "decadron for spinal cord compression",
      "dex for spinal cord compression", "dexamethasone for the spinal cord compression", "decadron for the spinal cord compression",
      "dex for the spinal cord compression", "dexamethasone for anaphylaxis", "decadron for anaphylaxis", "dex for anaphylaxis",
      "dexamethasone for the anaphylaxis", "decadron for the anaphylaxis", "dex for the anaphylaxis", "dexamethasone for angioedema",
      "decadron for angioedema", "dex for angioedema", "dexamethasone for the angioedema", "decadron for the angioedema", "dex for the angioedema",
      "dexamethasone for allergic reaction", "decadron for allergic reaction", "dex for allergic reaction", "dexamethasone for the allergic reaction",
      "decadron for the allergic reaction", "dex for the allergic reaction", "dexamethasone for hives", "decadron for hives", "dex for hives",
      "dexamethasone for the hives", "decadron for the hives", "dex for the hives", "dexamethasone for urticaria", "decadron for urticaria",
      "dex for urticaria", "dexamethasone for the urticaria", "decadron for the urticaria", "dex for the urticaria", "dexamethasone for nausea",
      "decadron for nausea", "dex for nausea", "dexamethasone for the nausea", "decadron for the nausea", "dex for the nausea", "dexamethasone for migraine",
      "decadron for migraine", "dex for migraine", "dexamethasone for the migraine", "decadron for the migraine", "dex for the migraine",
      "dexamethasone for headache", "decadron for headache", "dex for headache", "dexamethasone for the headache", "decadron for the headache",
      "dex for the headache", "dexamethasone for adrenal insufficiency", "decadron for adrenal insufficiency", "dex for adrenal insufficiency",
      "dexamethasone for the adrenal insufficiency", "decadron for the adrenal insufficiency", "dex for the adrenal insufficiency",
      "dexamethasone for adrenal crisis", "decadron for adrenal crisis", "dex for adrenal crisis", "dexamethasone for the adrenal crisis",
      "decadron for the adrenal crisis", "dex for the adrenal crisis", "dexamethasone for thyroid storm", "decadron for thyroid storm",
      "dex for thyroid storm", "dexamethasone for the thyroid storm", "decadron for the thyroid storm", "dex for the thyroid storm",
      "dexamethasone for myxedema", "decadron for myxedema", "dex for myxedema", "dexamethasone for the myxedema", "decadron for the myxedema",
      "dex for the myxedema", "dexamethasone for myxedema coma", "decadron for myxedema coma", "dex for myxedema coma", "dexamethasone for the myxedema coma",
      "decadron for the myxedema coma", "dex for the myxedema coma", "dexamethasone for pcp", "decadron for pcp", "dex for pcp", "dexamethasone for the pcp",
      "decadron for the pcp", "dex for the pcp", "dexamethasone for pneumocystis", "decadron for pneumocystis", "dex for pneumocystis",
      "dexamethasone for the pneumocystis", "decadron for the pneumocystis", "dex for the pneumocystis", "dexamethasone for covid", "decadron for covid",
      "dex for covid", "dexamethasone for the covid", "decadron for the covid", "dex for the covid", "dexamethasone for tb meningitis",
      "decadron for tb meningitis", "dex for tb meningitis", "dexamethasone for the tb meningitis", "decadron for the tb meningitis", "dex for the tb meningitis",
      "dexamethasone for bacterial meningitis", "decadron for bacterial meningitis", "dex for bacterial meningitis", "dexamethasone for the bacterial meningitis",
      "decadron for the bacterial meningitis", "dex for the bacterial meningitis", "dexamethasone for pneumococcal meningitis", "decadron for pneumococcal meningitis",
      "dex for pneumococcal meningitis", "dexamethasone for the pneumococcal meningitis", "decadron for the pneumococcal meningitis",
      "dex for the pneumococcal meningitis", "dexamethasone for h flu meningitis", "decadron for h flu meningitis", "dex for h flu meningitis",
      "dexamethasone for the h flu meningitis", "decadron for the h flu meningitis", "dex for the h flu meningitis", "dexamethasone for hib meningitis",
      "decadron for hib meningitis", "dex for hib meningitis", "dexamethasone for the hib meningitis", "decadron for the hib meningitis", "dex for the hib meningitis")
alias("hydrocortisone_bolus", "hydrocortisone", "solu cortef", "solucortef", "cortef", "stress dose steroids", "stress dose steroid", "stress dose hydrocortisone", "iv hydrocortisone")
alias("prednisone", "prednisone", "deltasone", "po prednisone", "oral prednisone", "oral steroids", "oral steroid", "po steroids", "po steroid", "prednisone burst", "steroid burst")
for p in ["steroids", "steroid", "corticosteroids", "corticosteroid", "glucocorticoid", "glucocorticoids", "a steroid", "some steroids"]:
    ambiguous(p, "methylprednisolone_bolus", "dexamethasone", "hydrocortisone_bolus", "prednisone")
for p in ["prednisolone", "orapred", "fludrocortisone", "florinef", "budesonide", "triamcinolone", "kenalog"]:
    unavailable(p, "Not in the catalog. Steroids available: methylprednisolone, dexamethasone, hydrocortisone, prednisone.")
alias("diphenhydramine", "diphenhydramine", "benadryl", "iv benadryl", "iv diphenhydramine", "antihistamine", "an antihistamine", "h1 blocker", "an h1 blocker", "h1 antagonist", "po benadryl", "im benadryl")
alias("famotidine_bolus", "famotidine_bolus", "pepcid", "iv pepcid", "iv famotidine", "h2 blocker", "an h2 blocker", "h2 antagonist", "h2 antihistamine", "po pepcid")
for p in ["ranitidine", "zantac", "cetirizine", "zyrtec", "loratadine", "claritin", "hydroxyzine", "atarax", "vistaril", "promethazine", "phenergan"]:
    unavailable(p, "Not in the catalog. Antihistamines available: diphenhydramine, famotidine.")
# GI
alias("esomeprazole_bolus", "esomeprazole", "nexium", "iv esomeprazole", "iv nexium", "esomeprazole bolus", "nexium bolus", "ppi", "a ppi", "proton pump inhibitor", "iv ppi", "iv proton pump inhibitor", "ppi bolus", "ppi drip", "ppi infusion", "esomeprazole drip", "esomeprazole infusion", "nexium drip", "nexium infusion")
for p in ["pantoprazole", "protonix", "omeprazole", "prilosec", "lansoprazole", "prevacid"]:
    unavailable(p, "Not in the catalog. The proton pump inhibitor available is esomeprazole.")
alias("glucagon", "glucagon", "iv glucagon", "im glucagon", "glucagon bolus", "glucagon push", "glucagon drip", "glucagon infusion", "glucagon gtt", "high dose glucagon", "glucagen")
alias("metoclopramide", "metoclopramide", "reglan", "iv reglan", "iv metoclopramide", "prokinetic", "a prokinetic")
alias("octreotide_bolus_infusion", "octreotide", "sandostatin", "octreotide bolus", "octreotide drip", "octreotide infusion", "octreotide gtt", "octreotide bolus and drip", "octreotide bolus then drip", "iv octreotide", "somatostatin", "somatostatin analog", "somatostatin analogue", "sandostatin drip", "sandostatin infusion")
alias("ondansetron", "ondansetron", "zofran", "iv zofran", "iv ondansetron", "odt zofran", "zofran odt", "ondansetron odt", "antiemetic", "an antiemetic", "antiemetics", "anti emetic", "something for nausea", "something for the nausea", "nausea medication", "nausea meds", "nausea med", "anti nausea", "anti nausea medication", "po zofran", "oral zofran", "zofran under the tongue")
for p in ["prochlorperazine", "compazine", "droperidol", "haldol for nausea", "scopolamine", "meclizine", "antivert", "trimethobenzamide", "tigan", "aprepitant", "emend"]:
    unavailable(p, "Not in the catalog. Antiemetics available: ondansetron, metoclopramide.")
for p in ["terlipressin", "terlivaz", "pantoprazole drip", "protonix drip", "sucralfate", "carafate", "lactulose", "rifaximin", "xifaxan", "erythromycin for gi bleed", "erythromycin before endoscopy"]:
    unavailable(p, "Not in the catalog. GI medications available: esomeprazole, famotidine, octreotide, ondansetron, metoclopramide, glucagon.")
# Antibiotics and antimicrobials
alias("acyclovir", "acyclovir", "zovirax", "iv acyclovir", "antiviral", "an antiviral", "antivirals", "acyclovir for hsv", "acyclovir for herpes", "valacyclovir", "valtrex")
alias("amoxicillin", "amoxicillin", "amoxil", "amox", "po amoxicillin", "oral amoxicillin", "amoxicillin clavulanate", "amox clav", "augmentin", "amoxicillin clav")
alias("amphotericin", "amphotericin", "amphotericin b", "ampho", "ampho b", "ambisome", "liposomal amphotericin", "liposomal ampho", "fungizone", "antifungal iv", "iv antifungal")
alias("ampicillin", "ampicillin", "amp", "iv ampicillin", "ampicillin for listeria", "amp for listeria", "listeria coverage", "cover listeria", "ampicillin sulbactam", "unasyn", "amp sulbactam")
alias("azithromycin", "azithromycin", "zithromax", "azithro", "z pak", "z pack", "zpak", "zpack", "iv azithromycin", "iv azithro", "po azithromycin", "po azithro", "macrolide", "a macrolide", "atypical coverage", "cover atypicals", "cover the atypicals", "atypicals")
alias("aztreonam", "aztreonam", "azactam")
alias("cefazolin", "cefazolin", "ancef", "kefzol", "iv cefazolin", "iv ancef", "first generation cephalosporin", "first gen cephalosporin", "1st generation cephalosporin", "1st gen cephalosporin")
alias("cefepime", "cefepime", "maxipime", "iv cefepime", "fourth generation cephalosporin", "fourth gen cephalosporin", "4th generation cephalosporin", "4th gen cephalosporin", "pseudomonal cephalosporin", "antipseudomonal cephalosporin")
alias("cefotaxime", "cefotaxime", "claforan", "iv cefotaxime")
alias("ceftriaxone", "ceftriaxone", "rocephin", "ctx", "iv ceftriaxone", "iv rocephin", "im ceftriaxone", "im rocephin", "ceftriaxone im", "rocephin im", "third generation cephalosporin", "third gen cephalosporin", "3rd generation cephalosporin", "3rd gen cephalosporin", "meningitis dose ceftriaxone", "meningitic dose ceftriaxone", "high dose ceftriaxone", "ceftriaxone 2 grams", "rocephin 2 grams", "ceftriaxone 1 gram", "rocephin 1 gram", "2 grams of ceftriaxone", "2 grams of rocephin", "1 gram of ceftriaxone", "1 gram of rocephin", "2 of ceftriaxone", "2 of rocephin", "two grams of ceftriaxone", "two grams of rocephin")
alias("chloramphenicol", "chloramphenicol", "chloromycetin")
alias("ciprofloxacin", "ciprofloxacin", "cipro", "iv cipro", "po cipro", "iv ciprofloxacin", "po ciprofloxacin")
alias("clindamycin", "clindamycin", "clinda", "cleocin", "iv clindamycin", "iv clinda", "po clindamycin", "po clinda", "clindamycin for toxin", "clinda for toxin", "clindamycin for toxin suppression", "clinda for toxin suppression", "toxin suppression", "antitoxin antibiotic")
alias("doxycycline", "doxycycline", "doxy", "vibramycin", "iv doxycycline", "iv doxy", "po doxycycline", "po doxy", "tetracycline", "a tetracycline", "doxycycline for rickettsia", "doxy for rickettsia", "doxycycline for rmsf", "doxy for rmsf", "doxycycline for lyme", "doxy for lyme", "doxycycline for tick borne", "doxy for tick borne")
alias("fluconazole", "fluconazole", "diflucan", "iv fluconazole", "po fluconazole", "azole", "an azole", "antifungal", "an antifungal", "antifungals")
for p in ["antifungal", "an antifungal", "antifungals"]:
    A["fluconazole"].remove(p); ambiguous(p, "fluconazole", "amphotericin")
alias("gentamicin", "gentamicin", "gent", "garamycin", "iv gentamicin", "iv gent", "aminoglycoside", "an aminoglycoside", "aminoglycosides", "gent for synergy", "gentamicin for synergy")
for p in ["tobramycin", "tobra", "amikacin"]:
    unavailable(p, "Not in the catalog. The aminoglycoside available is gentamicin.")
alias("levofloxacin", "levofloxacin", "levaquin", "levo floxacin", "iv levofloxacin", "iv levaquin", "po levofloxacin", "po levaquin", "respiratory fluoroquinolone", "a respiratory fluoroquinolone")
for p in ["fluoroquinolone", "a fluoroquinolone", "fluoroquinolones", "quinolone", "a quinolone", "quinolones"]:
    ambiguous(p, "levofloxacin", "ciprofloxacin", "moxifloxacin")
alias("meropenem", "meropenem", "merrem", "mero", "iv meropenem", "carbapenem", "a carbapenem", "carbapenems")
for p in ["imipenem", "primaxin", "ertapenem", "invanz", "doripenem"]:
    unavailable(p, "Not in the catalog. The carbapenem available is meropenem.")
alias("metronidazole", "metronidazole", "flagyl", "iv metronidazole", "iv flagyl", "po metronidazole", "po flagyl", "anaerobic coverage", "cover anaerobes", "anaerobes")
alias("minocycline", "minocycline", "minocin", "iv minocycline", "po minocycline")
alias("moxifloxacin", "moxifloxacin", "avelox", "iv moxifloxacin", "po moxifloxacin", "moxi")
alias("oseltamivir", "oseltamivir", "tamiflu", "po oseltamivir", "po tamiflu", "flu treatment", "influenza treatment", "treat the flu", "treat the influenza", "antiviral for flu", "antiviral for influenza", "neuraminidase inhibitor", "a neuraminidase inhibitor")
for p in ["baloxavir", "xofluza", "zanamivir", "relenza", "peramivir", "rapivab", "remdesivir", "veklury", "paxlovid", "nirmatrelvir", "molnupiravir"]:
    unavailable(p, "Not in the catalog. Antivirals available: oseltamivir, acyclovir.")
alias("penicillin_g", "penicillin", "penicillin g", "pen g", "iv penicillin", "iv pen g", "aqueous penicillin", "aqueous penicillin g", "pcn", "pcn g", "benzathine penicillin", "bicillin", "penicillin for syphilis", "penicillin for strep", "pen g for strep", "penicillin for gas")
alias("piperacillin_tazobactam", "piperacillin tazobactam", "pip tazo", "piptazo", "zosyn", "pip taz", "piperacillin and tazobactam", "iv zosyn", "iv pip tazo", "iv piperacillin tazobactam", "tazocin", "extended infusion zosyn", "extended infusion pip tazo")
alias("rifampin", "rifampin", "rifampicin", "rifadin", "po rifampin", "iv rifampin", "rifampin prophylaxis", "rifampin for prophylaxis", "meningococcal prophylaxis", "meningitis prophylaxis", "prophylaxis for contacts", "chemoprophylaxis for contacts")
alias("vancomycin", "vancomycin", "vanc", "vanco", "vancocin", "iv vancomycin", "iv vanc", "iv vanco", "vancomycin load", "vanc load", "vanco load", "load vancomycin", "load vanc", "load vanco", "vancomycin loading dose", "vanc loading dose", "vanco loading dose", "weight based vancomycin", "weight based vanc", "weight based vanco", "mrsa coverage", "cover mrsa", "cover for mrsa", "gram positive coverage", "cover gram positives", "po vancomycin", "po vanc", "po vanco", "oral vancomycin", "oral vanc", "oral vanco", "vancomycin for c diff", "vanc for c diff", "vanco for c diff", "po vanc for c diff", "po vancomycin for c diff")
for p in ["linezolid", "zyvox", "daptomycin", "cubicin", "ceftaroline", "teflaro", "tigecycline", "tygacil", "bactrim", "trimethoprim sulfamethoxazole", "tmp smx", "septra", "sulfamethoxazole", "nitrofurantoin", "macrobid", "cephalexin", "keflex", "cefuroxime", "ceftin", "cefoxitin", "cefotetan", "ceftazidime", "fortaz", "ceftazidime avibactam", "avycaz", "ceftolozane", "zerbaxa", "colistin", "polymyxin", "fidaxomicin", "dificid", "erythromycin", "clarithromycin", "biaxin", "streptomycin", "isoniazid", "inh", "ethambutol", "pyrazinamide", "ripe", "ripe therapy", "tb meds", "tb therapy", "anti tb", "antituberculous", "antituberculosis", "micafungin", "mycamine", "caspofungin", "cancidas", "anidulafungin", "eraxis", "voriconazole", "vfend", "posaconazole", "isavuconazole", "echinocandin", "an echinocandin", "nystatin", "clotrimazole", "ivermectin", "albendazole", "praziquantel", "artesunate", "quinine", "quinidine", "chloroquine", "hydroxychloroquine", "plaquenil", "atovaquone", "mefloquine", "primaquine", "malarone", "coartem", "artemether", "lumefantrine", "pentamidine", "dapsone", "monoclonal", "monoclonals", "monoclonal antibody", "monoclonal antibodies", "antitoxin", "botulinum antitoxin", "diphtheria antitoxin", "dat", "tetanus immune globulin", "tig", "hypertet", "rabies immune globulin", "rig", "hyperrab", "imogam", "rabies vaccine", "rabies vaccination", "rabies post exposure prophylaxis", "rabies pep", "hepatitis b immune globulin", "hbig", "hep b vaccine", "hepatitis b vaccine", "varicella immune globulin", "varizig", "vzig", "cmv immune globulin", "cytogam", "botulism immune globulin", "babybig", "antivenom", "antivenin", "crofab", "anavip", "anascorp", "coral snake antivenom", "black widow antivenom", "scorpion antivenom", "snake antivenom", "spider antivenom"]:
    unavailable(p, "Not in the catalog.")
for p in ["antibiotics", "antibiotic", "abx", "broad spectrum antibiotics", "broad spectrum", "empiric antibiotics", "empiric coverage", "broad spectrum coverage", "start antibiotics", "iv antibiotics", "an antibiotic", "some antibiotics", "antimicrobials", "antimicrobial", "sepsis antibiotics", "broaden antibiotics", "broaden coverage", "broaden the antibiotics", "broaden the coverage", "escalate antibiotics", "escalate the antibiotics", "escalate coverage", "escalate the coverage", "de escalate antibiotics", "narrow antibiotics", "narrow the antibiotics", "narrow coverage", "narrow the coverage", "antibiotics within the hour", "antibiotics in the first hour", "antibiotics stat", "antibiotics now", "antibiotics please", "cover gram negatives", "gram negative coverage", "pseudomonal coverage", "cover pseudomonas", "cover for pseudomonas", "antipseudomonal", "anti pseudomonal", "double cover pseudomonas", "double coverage", "double cover", "cephalosporin", "a cephalosporin", "cephalosporins", "beta lactam", "a beta lactam", "beta lactams", "cover strep", "strep coverage", "cover staph", "staph coverage", "cover for staph", "cover for strep", "skin flora coverage", "cover skin flora", "cover gi flora", "gi flora coverage", "cover gut flora", "gut flora coverage", "cover enterics", "enteric coverage", "cover for enterics", "cover for gram negatives", "cover for gram positives", "cover for anaerobes", "cover for atypicals", "cover for mrsa and pseudomonas", "cover mrsa and pseudomonas", "mrsa and pseudomonas coverage", "cover for mrsa and gram negatives", "cover mrsa and gram negatives", "mrsa and gram negative coverage"]:
    ambiguous(p, "vancomycin", "piperacillin_tazobactam", "cefepime", "ceftriaxone", "meropenem", "azithromycin", "metronidazole", "ampicillin", "gentamicin", "clindamycin", "levofloxacin", "cefazolin", "doxycycline", "aztreonam")
for cid, bad in [("ampicillin", ["ampicillin sulbactam", "unasyn", "amp sulbactam"]), ("amoxicillin", ["amoxicillin clavulanate", "amox clav", "augmentin", "amoxicillin clav"]),
                 ("acyclovir", ["valacyclovir", "valtrex"]), ("albuterol", ["xopenex", "levalbuterol"]), ("penicillin_g", ["benzathine penicillin", "bicillin"]),
                 ("doxycycline", ["tetracycline", "a tetracycline"])]:
    for p in bad:
        A[cid].remove(p); unavailable(p, "Not in the catalog; it is a different drug from the one the catalog carries, so it is not substituted.")
# OB/GYN
alias("methergine", "methergine", "methylergonovine", "methylergometrine", "im methergine", "methergine im")
alias("misoprostol", "misoprostol", "cytotec", "rectal misoprostol", "pr misoprostol", "buccal misoprostol", "sublingual misoprostol", "misoprostol pr", "misoprostol buccal")
alias("oxytocin_im_iv", "oxytocin", "pitocin", "pit", "oxytocin im", "oxytocin iv", "pitocin im", "pitocin iv", "im oxytocin", "iv oxytocin", "im pitocin", "iv pitocin", "oxytocin drip", "pitocin drip", "oxytocin infusion", "pitocin infusion", "oxytocin bolus", "pitocin bolus", "uterotonic", "a uterotonic", "uterotonics")
alias("rhogam", "rhogam", "rho gam", "rho d immune globulin", "rhod immune globulin", "anti d", "anti d immune globulin", "rh immune globulin", "rhig", "rh immunoglobulin", "anti d immunoglobulin", "rhophylac", "winrho")
for p in ["carboprost", "hemabate", "terbutaline for tocolysis", "tocolysis", "tocolytic", "nifedipine for tocolysis", "betamethasone", "celestone", "antenatal steroids", "fetal lung maturity steroids", "methotrexate", "mtx", "tranexamic acid for pph"]:
    unavailable(p, "Not in the catalog. OB medications available: oxytocin, methergine, misoprostol, RhoGAM, magnesium sulfate, tranexamic acid.")
# Tox
alias("activated_charcoal", "activated charcoal", "charcoal", "ac", "po charcoal", "charcoal by ng", "charcoal via ng", "charcoal through the ng", "charcoal down the ng", "multi dose charcoal", "multidose charcoal", "mdac", "single dose charcoal", "gi decontamination", "gut decontamination", "decontaminate the gut")
alias("digoxin_immune_fab", "digoxin immune fab", "dig fab", "digifab", "digibind", "dig immune fab", "digoxin fab", "digoxin antibody", "digoxin antibodies", "dig antibodies", "dig antibody", "fab fragments", "digoxin fab fragments", "dig fab fragments", "antidote for digoxin", "digoxin antidote", "dig antidote", "reverse the digoxin", "reverse digoxin", "reverse the dig", "reverse dig")
alias("flumazenil", "flumazenil", "romazicon", "benzo reversal", "benzodiazepine reversal", "reverse the benzos", "reverse the benzo", "reverse benzos", "reverse the benzodiazepine", "reverse benzodiazepines", "benzo antidote", "benzodiazepine antidote", "benzo antagonist", "benzodiazepine antagonist", "reverse the midazolam", "reverse the versed", "reverse the lorazepam", "reverse the ativan", "reverse versed", "reverse midazolam", "reverse ativan", "reverse lorazepam")
alias("fomepizole", "fomepizole", "antizol", "4 mp", "4mp", "four mp", "4 methylpyrazole", "methylpyrazole", "alcohol dehydrogenase inhibitor", "adh inhibitor", "block alcohol dehydrogenase", "block adh", "toxic alcohol antidote", "antidote for methanol", "antidote for ethylene glycol", "antidote for toxic alcohol", "antidote for toxic alcohols", "methanol antidote", "ethylene glycol antidote", "antifreeze antidote")
alias("intralipid", "intralipid", "lipid emulsion", "lipid emulsion therapy", "lipid rescue", "intravenous lipid emulsion", "ile", "iv lipid", "iv lipids", "lipids", "20 percent lipid", "20 percent intralipid", "20 percent lipid emulsion", "lipid bolus", "intralipid bolus", "lipid infusion", "intralipid infusion", "lipid drip", "intralipid drip", "fat emulsion", "lipid sink", "last resort lipids", "lipid for last", "lipid for the last", "lipid for local anesthetic toxicity", "lipid for bupivacaine", "lipid for bupivacaine toxicity", "lipid for tca overdose", "lipid for calcium channel blocker overdose", "lipid for ccb overdose", "lipid for beta blocker overdose", "lipid for bb overdose", "lipid for lipophilic overdose", "lipid for lipophilic drug overdose", "lipid for lipophilic drug", "lipid for lipophilic")
alias("n_acetylcysteine", "n acetylcysteine", "acetylcysteine", "nac", "n a c", "mucomyst", "acetadote", "iv nac", "iv acetylcysteine", "iv n acetylcysteine", "po nac", "oral nac", "po acetylcysteine", "oral acetylcysteine", "nac drip", "nac infusion", "acetylcysteine drip", "acetylcysteine infusion", "nac protocol", "acetylcysteine protocol", "21 hour nac", "21 hour protocol", "21 hour acetylcysteine", "twenty one hour nac", "twenty one hour protocol", "twenty one hour acetylcysteine", "3 bag nac", "three bag nac", "3 bag protocol", "three bag protocol", "2 bag nac", "two bag nac", "2 bag protocol", "two bag protocol", "acetaminophen antidote", "tylenol antidote", "apap antidote", "antidote for acetaminophen", "antidote for tylenol", "antidote for apap", "nac for acetaminophen", "nac for tylenol", "nac for apap", "acetylcysteine for acetaminophen", "acetylcysteine for tylenol", "acetylcysteine for apap", "nac for the acetaminophen", "nac for the tylenol", "nac for the apap", "start nac", "start acetylcysteine", "start n acetylcysteine", "start the nac", "start the acetylcysteine", "start the n acetylcysteine", "start nac protocol", "start the nac protocol", "start acetylcysteine protocol", "start the acetylcysteine protocol")
alias("na_bicarbonate_bolus", "bicarb bolus", "bicarbonate bolus", "sodium bicarbonate bolus", "sodium bicarb bolus", "amp of bicarb", "amp of bicarbonate", "amp of sodium bicarbonate", "amp of sodium bicarb", "an amp of bicarb", "an amp of bicarbonate", "an amp of sodium bicarbonate", "an amp of sodium bicarb", "amps of bicarb", "amps of bicarbonate", "amps of sodium bicarbonate", "amps of sodium bicarb", "two amps of bicarb", "2 amps of bicarb", "three amps of bicarb", "3 amps of bicarb", "bicarb push", "bicarbonate push", "sodium bicarbonate push", "sodium bicarb push", "push bicarb", "push bicarbonate", "push sodium bicarbonate", "push sodium bicarb", "push an amp of bicarb", "push an amp of bicarbonate", "push an amp of sodium bicarbonate", "push an amp of sodium bicarb", "iv bicarb push", "iv bicarbonate push", "iv sodium bicarbonate push", "iv sodium bicarb push", "bicarb amp", "bicarbonate amp", "sodium bicarbonate amp", "sodium bicarb amp", "bicarb amps", "bicarbonate amps", "sodium bicarbonate amps", "sodium bicarb amps", "bicarb 50", "bicarbonate 50", "sodium bicarbonate 50", "sodium bicarb 50", "bicarb 50 meq", "bicarbonate 50 meq", "sodium bicarbonate 50 meq", "sodium bicarb 50 meq", "50 of bicarb", "50 of bicarbonate", "50 of sodium bicarbonate", "50 of sodium bicarb", "50 meq of bicarb", "50 meq of bicarbonate", "50 meq of sodium bicarbonate", "50 meq of sodium bicarb", "bicarb 100", "bicarbonate 100", "sodium bicarbonate 100", "sodium bicarb 100", "bicarb 100 meq", "bicarbonate 100 meq", "sodium bicarbonate 100 meq", "sodium bicarb 100 meq", "100 of bicarb", "100 of bicarbonate", "100 of sodium bicarbonate", "100 of sodium bicarb", "100 meq of bicarb", "100 meq of bicarbonate", "100 meq of sodium bicarbonate", "100 meq of sodium bicarb", "bicarb 1 meq per kilo", "bicarbonate 1 meq per kilo", "sodium bicarbonate 1 meq per kilo", "sodium bicarb 1 meq per kilo", "1 meq per kilo bicarb", "1 meq per kilo bicarbonate", "1 meq per kilo sodium bicarbonate", "1 meq per kilo sodium bicarb", "bicarb 1 per kilo", "bicarbonate 1 per kilo", "sodium bicarbonate 1 per kilo", "sodium bicarb 1 per kilo", "1 per kilo bicarb", "1 per kilo bicarbonate", "1 per kilo sodium bicarbonate", "1 per kilo sodium bicarb", "bicarb 2 meq per kilo", "bicarbonate 2 meq per kilo", "sodium bicarbonate 2 meq per kilo", "sodium bicarb 2 meq per kilo", "2 meq per kilo bicarb", "2 meq per kilo bicarbonate", "2 meq per kilo sodium bicarbonate", "2 meq per kilo sodium bicarb", "bicarb 2 per kilo", "bicarbonate 2 per kilo", "sodium bicarbonate 2 per kilo", "sodium bicarb 2 per kilo", "2 per kilo bicarb", "2 per kilo bicarbonate", "2 per kilo sodium bicarbonate", "2 per kilo sodium bicarb", "another amp of bicarb", "another amp of bicarbonate", "another amp of sodium bicarbonate", "another amp of sodium bicarb", "repeat the bicarb", "repeat the bicarbonate", "repeat the sodium bicarbonate", "repeat the sodium bicarb", "repeat bicarb", "repeat bicarbonate", "repeat sodium bicarbonate", "repeat sodium bicarb", "one more amp of bicarb", "one more amp of bicarbonate", "one more amp of sodium bicarbonate", "one more amp of sodium bicarb", "1 more amp of bicarb", "second amp of bicarb", "second amp of bicarbonate", "second amp of sodium bicarbonate", "second amp of sodium bicarb", "bicarb for the qrs", "bicarbonate for the qrs", "sodium bicarbonate for the qrs", "sodium bicarb for the qrs", "bicarb for qrs widening", "bicarbonate for qrs widening", "sodium bicarbonate for qrs widening", "sodium bicarb for qrs widening", "bicarb for the wide qrs", "bicarbonate for the wide qrs", "sodium bicarbonate for the wide qrs", "sodium bicarb for the wide qrs", "bicarb for wide qrs", "bicarbonate for wide qrs", "sodium bicarbonate for wide qrs", "sodium bicarb for wide qrs", "bicarb for tca", "bicarbonate for tca", "sodium bicarbonate for tca", "sodium bicarb for tca", "bicarb for the tca", "bicarbonate for the tca", "sodium bicarbonate for the tca", "sodium bicarb for the tca", "bicarb for tca overdose", "bicarbonate for tca overdose", "sodium bicarbonate for tca overdose", "sodium bicarb for tca overdose", "bicarb for the tca overdose", "bicarbonate for the tca overdose", "sodium bicarbonate for the tca overdose", "sodium bicarb for the tca overdose", "bicarb for sodium channel blockade", "bicarbonate for sodium channel blockade", "sodium bicarbonate for sodium channel blockade", "sodium bicarb for sodium channel blockade", "bicarb for the sodium channel blockade", "bicarbonate for the sodium channel blockade", "sodium bicarbonate for the sodium channel blockade", "sodium bicarb for the sodium channel blockade", "bicarb for hyperkalemia", "bicarbonate for hyperkalemia", "sodium bicarbonate for hyperkalemia", "sodium bicarb for hyperkalemia", "bicarb for the hyperkalemia", "bicarbonate for the hyperkalemia", "sodium bicarbonate for the hyperkalemia", "sodium bicarb for the hyperkalemia", "bicarb for the potassium", "bicarbonate for the potassium", "sodium bicarbonate for the potassium", "sodium bicarb for the potassium", "bicarb for acidosis", "bicarbonate for acidosis", "sodium bicarbonate for acidosis", "sodium bicarb for acidosis", "bicarb for the acidosis", "bicarbonate for the acidosis", "sodium bicarbonate for the acidosis", "sodium bicarb for the acidosis", "bicarb for the ph", "bicarbonate for the ph", "sodium bicarbonate for the ph", "sodium bicarb for the ph", "bicarb for the arrest", "bicarbonate for the arrest", "sodium bicarbonate for the arrest", "sodium bicarb for the arrest", "bicarb for arrest", "bicarbonate for arrest", "sodium bicarbonate for arrest", "sodium bicarb for arrest", "bicarb for cardiac arrest", "bicarbonate for cardiac arrest", "sodium bicarbonate for cardiac arrest", "sodium bicarb for cardiac arrest", "bicarb for the cardiac arrest", "bicarbonate for the cardiac arrest", "sodium bicarbonate for the cardiac arrest", "sodium bicarb for the cardiac arrest")
alias("na_bicarbonate_infusion", "bicarb drip", "bicarbonate drip", "sodium bicarbonate drip", "sodium bicarb drip", "bicarb infusion", "bicarbonate infusion", "sodium bicarbonate infusion", "sodium bicarb infusion", "bicarb gtt", "bicarbonate gtt", "sodium bicarbonate gtt", "sodium bicarb gtt", "bicarb in d5w", "bicarbonate in d5w", "sodium bicarbonate in d5w", "sodium bicarb in d5w", "3 amps of bicarb in d5w", "three amps of bicarb in d5w", "3 amps of bicarb in a liter of d5w", "three amps of bicarb in a liter of d5w", "3 amps in d5w", "three amps in d5w", "150 of bicarb in d5w", "150 meq of bicarb in d5w", "150 meq bicarb in d5w", "150 of bicarb in a liter of d5w", "150 meq of bicarb in a liter of d5w", "bicarb in a liter of d5w", "bicarbonate in a liter of d5w", "sodium bicarbonate in a liter of d5w", "sodium bicarb in a liter of d5w", "isotonic bicarb", "isotonic bicarbonate", "isotonic sodium bicarbonate", "isotonic sodium bicarb", "isotonic bicarb drip", "isotonic bicarbonate drip", "isotonic sodium bicarbonate drip", "isotonic sodium bicarb drip", "isotonic bicarb infusion", "isotonic bicarbonate infusion", "isotonic sodium bicarbonate infusion", "isotonic sodium bicarb infusion", "bicarb at 150", "bicarbonate at 150", "sodium bicarbonate at 150", "sodium bicarb at 150", "bicarb at 200", "bicarbonate at 200", "sodium bicarbonate at 200", "sodium bicarb at 200", "bicarb at 250", "bicarbonate at 250", "sodium bicarbonate at 250", "sodium bicarb at 250", "bicarb at 100", "bicarbonate at 100", "sodium bicarbonate at 100", "sodium bicarb at 100", "bicarb at 125", "bicarbonate at 125", "sodium bicarbonate at 125", "sodium bicarb at 125", "continuous bicarb", "continuous bicarbonate", "continuous sodium bicarbonate", "continuous sodium bicarb", "bicarb continuous", "bicarbonate continuous", "sodium bicarbonate continuous", "sodium bicarb continuous", "start a bicarb drip", "start a bicarbonate drip", "start a sodium bicarbonate drip", "start a sodium bicarb drip", "start bicarb drip", "start bicarbonate drip", "start sodium bicarbonate drip", "start sodium bicarb drip", "start a bicarb infusion", "start a bicarbonate infusion", "start a sodium bicarbonate infusion", "start a sodium bicarb infusion", "start bicarb infusion", "start bicarbonate infusion", "start sodium bicarbonate infusion", "start sodium bicarb infusion", "hang bicarb", "hang bicarbonate", "hang sodium bicarbonate", "hang sodium bicarb", "hang a bicarb drip", "hang a bicarbonate drip", "hang a sodium bicarbonate drip", "hang a sodium bicarb drip", "alkalinize the urine", "alkalinise the urine", "urinary alkalinization", "urinary alkalinisation", "urine alkalinization", "urine alkalinisation", "alkalinize the serum", "alkalinise the serum", "serum alkalinization", "serum alkalinisation", "alkalinization", "alkalinisation", "alkalinize", "alkalinise", "bicarb for salicylates", "bicarbonate for salicylates", "sodium bicarbonate for salicylates", "sodium bicarb for salicylates", "bicarb for the salicylates", "bicarbonate for the salicylates", "sodium bicarbonate for the salicylates", "sodium bicarb for the salicylates", "bicarb for salicylate", "bicarbonate for salicylate", "sodium bicarbonate for salicylate", "sodium bicarb for salicylate", "bicarb for the salicylate", "bicarbonate for the salicylate", "sodium bicarbonate for the salicylate", "sodium bicarb for the salicylate", "bicarb for aspirin", "bicarbonate for aspirin", "sodium bicarbonate for aspirin", "sodium bicarb for aspirin", "bicarb for the aspirin", "bicarbonate for the aspirin", "sodium bicarbonate for the aspirin", "sodium bicarb for the aspirin", "bicarb for aspirin overdose", "bicarbonate for aspirin overdose", "sodium bicarbonate for aspirin overdose", "sodium bicarb for aspirin overdose", "bicarb for the aspirin overdose", "bicarbonate for the aspirin overdose", "sodium bicarbonate for the aspirin overdose", "sodium bicarb for the aspirin overdose", "bicarb for salicylate overdose", "bicarbonate for salicylate overdose", "sodium bicarbonate for salicylate overdose", "sodium bicarb for salicylate overdose", "bicarb for the salicylate overdose", "bicarbonate for the salicylate overdose", "sodium bicarbonate for the salicylate overdose", "sodium bicarb for the salicylate overdose", "bicarb for rhabdo", "bicarbonate for rhabdo", "sodium bicarbonate for rhabdo", "sodium bicarb for rhabdo", "bicarb for the rhabdo", "bicarbonate for the rhabdo", "sodium bicarbonate for the rhabdo", "sodium bicarb for the rhabdo", "bicarb for rhabdomyolysis", "bicarbonate for rhabdomyolysis", "sodium bicarbonate for rhabdomyolysis", "sodium bicarb for rhabdomyolysis", "bicarb for the rhabdomyolysis", "bicarbonate for the rhabdomyolysis", "sodium bicarbonate for the rhabdomyolysis", "sodium bicarb for the rhabdomyolysis")
for p in ["bicarb", "bicarbonate", "sodium bicarbonate", "sodium bicarb", "nahco3", "na bicarb", "na bicarbonate", "iv bicarb", "iv bicarbonate", "iv sodium bicarbonate", "iv sodium bicarb", "some bicarb", "some bicarbonate", "give bicarb", "give bicarbonate", "bicarb please", "bicarbonate please", "bicarb stat", "bicarbonate stat", "bicarb now", "bicarbonate now"]:
    ambiguous(p, "na_bicarbonate_bolus", "na_bicarbonate_infusion")
alias("naloxone_bolus", "naloxone", "narcan", "naloxone bolus", "narcan bolus", "naloxone push", "narcan push", "iv naloxone", "iv narcan", "im naloxone", "im narcan", "intranasal naloxone", "intranasal narcan", "in naloxone", "in narcan", "naloxone drip", "narcan drip", "naloxone infusion", "narcan infusion", "naloxone gtt", "narcan gtt", "opioid reversal", "opiate reversal", "reverse the opioid", "reverse the opioids", "reverse the opiate", "reverse the opiates", "reverse opioids", "reverse opiates", "opioid antidote", "opiate antidote", "opioid antagonist", "opiate antagonist", "reverse the fentanyl", "reverse the morphine", "reverse the heroin", "reverse fentanyl", "reverse morphine", "reverse heroin", "reverse the narcotics", "reverse narcotics", "narcotic reversal", "narcotic antagonist", "narcotic antidote")
alias("physostigmine", "physostigmine", "physo", "antilirium", "anticholinergic antidote", "antidote for anticholinergic", "antidote for anticholinergics", "antidote for anticholinergic toxicity", "antidote for anticholinergic toxidrome", "reverse the anticholinergic", "reverse the anticholinergics", "reverse anticholinergic", "reverse anticholinergics", "reverse the anticholinergic toxidrome", "reverse the anticholinergic toxicity", "reverse the benadryl", "reverse benadryl", "reverse the diphenhydramine", "reverse diphenhydramine", "reverse the antihistamine", "reverse antihistamine", "reverse the antihistamines", "reverse antihistamines", "cholinesterase inhibitor", "acetylcholinesterase inhibitor", "reversible cholinesterase inhibitor", "reversible acetylcholinesterase inhibitor")
alias("pralidoxime_2_pam", "pralidoxime", "2 pam", "2pam", "two pam", "protopam", "pralidoxime chloride", "2 pam chloride", "pam", "oxime", "an oxime", "oximes", "organophosphate antidote", "antidote for organophosphate", "antidote for organophosphates", "antidote for organophosphate poisoning", "antidote for nerve agent", "antidote for nerve agents", "nerve agent antidote", "cholinesterase reactivator", "acetylcholinesterase reactivator", "reactivate cholinesterase", "reactivate acetylcholinesterase", "reactivate the cholinesterase", "reactivate the acetylcholinesterase", "duodote", "mark 1", "mark one", "mark 1 kit", "mark one kit", "atropen and pralidoxime", "atropine and pralidoxime", "atropine and 2 pam", "atropine and 2pam", "atropine and two pam", "atropine plus pralidoxime", "atropine plus 2 pam", "atropine plus 2pam", "atropine plus two pam", "pralidoxime and atropine", "2 pam and atropine", "2pam and atropine", "two pam and atropine", "pralidoxime plus atropine", "2 pam plus atropine", "2pam plus atropine", "two pam plus atropine")
for p in ["atropine and pralidoxime", "atropine and 2 pam", "atropine and 2pam", "atropine and two pam", "atropine plus pralidoxime", "atropine plus 2 pam", "atropine plus 2pam", "atropine plus two pam", "pralidoxime and atropine", "2 pam and atropine", "2pam and atropine", "two pam and atropine", "pralidoxime plus atropine", "2 pam plus atropine", "2pam plus atropine", "two pam plus atropine", "duodote", "mark 1", "mark one", "mark 1 kit", "mark one kit", "atropen and pralidoxime"]:
    A["pralidoxime_2_pam"].remove(p); expand(p, "atropine_bolus", "pralidoxime_2_pam")
alias("thiamine", "thiamine", "vitamin b1", "b1", "vitamin b 1", "b 1", "iv thiamine", "im thiamine", "po thiamine", "oral thiamine", "high dose thiamine", "thiamine 100", "thiamine 500", "100 of thiamine", "500 of thiamine", "thiamine 100 milligrams", "thiamine 500 milligrams", "thiamine 100 mg", "thiamine 500 mg", "100 milligrams of thiamine", "500 milligrams of thiamine", "100 mg of thiamine", "500 mg of thiamine", "thiamine before glucose", "thiamine before dextrose", "thiamine before the glucose", "thiamine before the dextrose", "thiamine before d50", "thiamine before the d50", "thiamine first", "thiamine before sugar", "thiamine before the sugar", "thiamine for wernicke", "thiamine for wernickes", "thiamine for the wernicke", "thiamine for the wernickes", "thiamine for wernicke encephalopathy", "thiamine for wernickes encephalopathy", "thiamine for the wernicke encephalopathy", "thiamine for the wernickes encephalopathy", "thiamine for alcohol", "thiamine for the alcohol", "thiamine for alcoholism", "thiamine for the alcoholism", "thiamine for alcohol withdrawal", "thiamine for the alcohol withdrawal", "thiamine for etoh", "thiamine for the etoh", "thiamine for etoh withdrawal", "thiamine for the etoh withdrawal", "thiamine for malnutrition", "thiamine for the malnutrition", "thiamine for refeeding", "thiamine for the refeeding", "thiamine for refeeding syndrome", "thiamine for the refeeding syndrome", "thiamine for beriberi", "thiamine for the beriberi", "thiamine for wet beriberi", "thiamine for the wet beriberi", "thiamine for dry beriberi", "thiamine for the dry beriberi", "banana bag", "a banana bag", "rally pack", "a rally pack", "thiamine folate and multivitamin", "thiamine folate multivitamin", "thiamine and folate", "thiamine folate", "thiamine and a multivitamin", "thiamine and multivitamin", "thiamine multivitamin")
for p in ["banana bag", "a banana bag", "rally pack", "a rally pack", "thiamine folate and multivitamin", "thiamine folate multivitamin", "thiamine and folate", "thiamine folate", "thiamine and a multivitamin", "thiamine and multivitamin", "thiamine multivitamin"]:
    A["thiamine"].remove(p); unavailable(p, "Folate and the multivitamin are not in the catalog; thiamine is.")
for p in ["folate", "folic acid", "multivitamin", "mvi", "vitamin k", "phytonadione", "aquamephyton", "vitamin c", "ascorbic acid", "vitamin b12", "cyanocobalamin", "b12", "pyridoxine", "vitamin b6", "b6", "hydroxocobalamin", "cyanokit", "sodium thiosulfate", "sodium nitrite", "amyl nitrite", "cyanide antidote", "cyanide kit", "dimercaprol", "edta", "succimer", "chemet", "deferoxamine", "desferal", "octreotide for sulfonylurea", "glucarpidase", "leucovorin", "uridine", "dantrolene", "cyproheptadine", "periactin", "bromocriptine", "l carnitine", "carnitine", "levocarnitine", "carnitor", "silibinin", "legalon", "botulism antitoxin", "digoxin specific antibody", "insulin for ccb overdose", "high dose insulin", "hdi", "high dose insulin euglycemia", "hie", "hiet", "glucagon for beta blocker", "calcium for ccb", "pyridoxine for isoniazid", "b6 for inh", "hyperbaric oxygen", "hyperbaric", "hbo", "hbot", "hyperbaric chamber", "dive chamber", "octreotide for hypoglycemia", "diazoxide", "dextrose gel", "glucose gel", "oral glucose", "oral glucose gel", "juice", "orange juice", "sugar by mouth", "glucose by mouth"]:
    unavailable(p, "Not in the catalog.")
# Psych
alias("haloperidol", "haloperidol", "haldol", "im haloperidol", "im haldol", "iv haloperidol", "iv haldol", "haldol im", "haldol iv", "haloperidol im", "haloperidol iv", "b52", "b 52", "five and two", "5 and 2", "haldol and ativan", "haloperidol and lorazepam", "haldol ativan", "haldol and benadryl", "haldol ativan benadryl", "haldol ativan and benadryl", "antipsychotic", "an antipsychotic", "antipsychotics", "typical antipsychotic", "a typical antipsychotic", "butyrophenone")
for p in ["b52", "b 52", "five and two", "5 and 2", "haldol and ativan", "haloperidol and lorazepam", "haldol ativan"]:
    A["haloperidol"].remove(p); expand(p, "haloperidol", "lorazepam_bolus")
for p in ["haldol and benadryl", "haldol ativan benadryl", "haldol ativan and benadryl"]:
    A["haloperidol"].remove(p); expand(p, "haloperidol", "lorazepam_bolus", "diphenhydramine")
for p in ["antipsychotic", "an antipsychotic", "antipsychotics"]:
    A["haloperidol"].remove(p); ambiguous(p, "haloperidol", "olanzapine", "ziprasidone")
alias("olanzapine", "olanzapine", "zyprexa", "im olanzapine", "im zyprexa", "olanzapine im", "zyprexa im", "zydis", "olanzapine odt", "zyprexa zydis", "olanzapine zydis", "po olanzapine", "po zyprexa", "atypical antipsychotic", "an atypical antipsychotic", "atypical")
for p in ["atypical antipsychotic", "an atypical antipsychotic", "atypical"]:
    A["olanzapine"].remove(p); ambiguous(p, "olanzapine", "ziprasidone")
alias("ziprasidone", "ziprasidone", "geodon", "im ziprasidone", "im geodon", "ziprasidone im", "geodon im")
for p in ["quetiapine", "seroquel", "risperidone", "risperdal", "aripiprazole", "abilify", "chlorpromazine", "thorazine", "droperidol", "inapsine", "dexmedetomidine", "precedex"]:
    unavailable(p, "Not in the catalog. Antipsychotics available: haloperidol, olanzapine, ziprasidone.")
# Miscellaneous
alias("calcium_chloride_bolus", "calcium chloride", "calcium chloride bolus", "cacl", "cacl2", "ca chloride", "calcium chloride push", "amp of calcium", "an amp of calcium", "amp of calcium chloride", "an amp of calcium chloride", "amps of calcium", "amps of calcium chloride", "iv calcium", "calcium iv", "calcium push", "push calcium", "calcium bolus", "calcium for the potassium", "calcium for hyperkalemia", "calcium for the hyperkalemia", "calcium to stabilize the membrane", "calcium to stabilize the myocardium", "stabilize the membrane", "stabilize the myocardium", "membrane stabilization", "membrane stabilizer", "calcium for the membrane", "calcium for membrane stabilization", "calcium for ccb", "calcium for ccb overdose", "calcium for the ccb overdose", "calcium for calcium channel blocker", "calcium for calcium channel blocker overdose", "calcium for the calcium channel blocker overdose", "calcium for hypocalcemia", "calcium for the hypocalcemia", "calcium for the low calcium", "calcium for low calcium", "calcium for hydrofluoric acid", "calcium for hf", "calcium for the hf", "calcium for hf burn", "calcium for hf burns", "calcium for the hf burn", "calcium for the hf burns", "calcium for hydrofluoric", "calcium for the hydrofluoric", "calcium for hydrofluoric acid burn", "calcium for hydrofluoric acid burns", "calcium for the hydrofluoric acid burn", "calcium for the hydrofluoric acid burns", "calcium for magnesium toxicity", "calcium for mag toxicity", "calcium for the magnesium toxicity", "calcium for the mag toxicity", "calcium for hypermagnesemia", "calcium for the hypermagnesemia", "calcium for massive transfusion", "calcium for the massive transfusion", "calcium for mtp", "calcium for the mtp", "calcium with the blood", "calcium with blood", "calcium with the transfusion", "calcium with transfusion", "calcium with the blood products", "calcium with blood products", "calcium replacement", "replace calcium", "replace the calcium", "calcium repletion", "replete calcium", "replete the calcium", "give calcium", "some calcium", "calcium please", "calcium stat", "calcium now", "calcium gluconate", "calcium gluconate bolus", "ca gluconate", "gluconate", "amp of calcium gluconate", "an amp of calcium gluconate", "amps of calcium gluconate", "calcium gluconate push", "gram of calcium gluconate", "a gram of calcium gluconate", "1 gram of calcium gluconate", "one gram of calcium gluconate", "2 grams of calcium gluconate", "two grams of calcium gluconate", "3 grams of calcium gluconate", "three grams of calcium gluconate", "calcium gluconate 1 gram", "calcium gluconate 2 grams", "calcium gluconate 3 grams", "calcium gluconate 10 percent", "10 percent calcium gluconate", "calcium chloride 10 percent", "10 percent calcium chloride", "calcium chloride 1 gram", "calcium chloride 1 g", "1 gram of calcium chloride", "one gram of calcium chloride", "gram of calcium chloride", "a gram of calcium chloride", "calcium chloride 500", "calcium chloride 500 mg", "500 of calcium chloride", "500 mg of calcium chloride", "calcium chloride 500 milligrams", "500 milligrams of calcium chloride")
for p in ["calcium gluconate", "calcium gluconate bolus", "ca gluconate", "gluconate", "amp of calcium gluconate", "an amp of calcium gluconate", "amps of calcium gluconate", "calcium gluconate push", "gram of calcium gluconate", "a gram of calcium gluconate", "1 gram of calcium gluconate", "one gram of calcium gluconate", "2 grams of calcium gluconate", "two grams of calcium gluconate", "3 grams of calcium gluconate", "three grams of calcium gluconate", "calcium gluconate 1 gram", "calcium gluconate 2 grams", "calcium gluconate 3 grams", "calcium gluconate 10 percent", "10 percent calcium gluconate"]:
    A["calcium_chloride_bolus"].remove(p); unavailable(p, "Calcium gluconate is not in the catalog; calcium chloride is. Not substituted.")
for p in ["give calcium", "some calcium", "calcium please", "calcium stat", "calcium now", "calcium replacement", "replace calcium", "replace the calcium", "calcium repletion", "replete calcium", "replete the calcium"]:
    A["calcium_chloride_bolus"].remove(p)
# The author's rule: a bare "calcium" is the level. Anything with "give", "push", "amp",
# "iv", "bolus" or a reason attached is the drug, and those are the rows above.
alias("calcium_chloride_bolus", "give calcium", "calcium replacement", "replace calcium", "replace the calcium", "calcium repletion", "replete calcium", "replete the calcium")
alias("colchicine", "colchicine", "colcrys", "po colchicine")
alias("d50_bolus", "d50", "d 50", "amp of d50", "an amp of d50", "amps of d50", "half an amp of d50", "half amp of d50", "d50 bolus", "d50 push", "push d50", "dextrose", "iv dextrose", "dextrose bolus", "dextrose push", "push dextrose", "50 percent dextrose", "dextrose 50", "dextrose 50 percent", "d 50 w", "d50w", "iv glucose", "glucose bolus", "glucose push", "push glucose", "sugar bolus", "iv sugar", "d10 bolus", "d10 push", "d25", "d 25", "d25 bolus", "d10 bolus for hypoglycemia", "dextrose for hypoglycemia", "dextrose for the hypoglycemia", "d50 for hypoglycemia", "d50 for the hypoglycemia", "dextrose for the sugar", "d50 for the sugar", "dextrose for low sugar", "d50 for low sugar", "dextrose for the low sugar", "d50 for the low sugar", "dextrose for low glucose", "d50 for low glucose", "dextrose for the low glucose", "d50 for the low glucose", "one amp of d50", "1 amp of d50", "two amps of d50", "2 amps of d50", "25 grams of dextrose", "25 grams of d50", "25 of d50", "25 of dextrose", "50 of d50", "50 of dextrose", "50 ml of d50", "50 cc of d50", "25 grams dextrose", "dextrose 25 grams", "d50 25 grams", "d50 50 ml", "d50 50 cc", "d50 50", "dextrose 12 5", "dextrose 12 5 grams", "12 5 grams of dextrose", "12 5 of dextrose", "half an amp", "half amp", "an amp of dextrose", "amp of dextrose", "amps of dextrose", "an amp of sugar", "amp of sugar", "amp of glucose", "an amp of glucose")
for p in ["half an amp", "half amp"]:
    A["d50_bolus"].remove(p)
alias("furosemide_40_mg_iv", "furosemide", "lasix", "iv furosemide", "iv lasix", "furosemide iv", "lasix iv", "furosemide bolus", "lasix bolus", "furosemide push", "lasix push", "push lasix", "push furosemide", "loop diuretic", "a loop diuretic", "loop diuretics", "diuretic", "a diuretic", "diuretics", "diurese", "diuresis", "diurese the patient", "diurese them", "diurese him", "diurese her", "start diuresis", "iv diuretic", "iv diuretics", "iv diuresis", "frusemide", "furosemide 40", "lasix 40", "40 of furosemide", "40 of lasix", "furosemide 40 milligrams", "lasix 40 milligrams", "furosemide 40 mg", "lasix 40 mg", "40 milligrams of furosemide", "40 milligrams of lasix", "40 mg of furosemide", "40 mg of lasix", "furosemide 80", "lasix 80", "80 of furosemide", "80 of lasix", "furosemide 80 milligrams", "lasix 80 milligrams", "furosemide 80 mg", "lasix 80 mg", "80 milligrams of furosemide", "80 milligrams of lasix", "80 mg of furosemide", "80 mg of lasix", "furosemide 20", "lasix 20", "20 of furosemide", "20 of lasix", "furosemide 20 milligrams", "lasix 20 milligrams", "furosemide 20 mg", "lasix 20 mg", "20 milligrams of furosemide", "20 milligrams of lasix", "20 mg of furosemide", "20 mg of lasix", "furosemide 100", "lasix 100", "100 of furosemide", "100 of lasix", "furosemide 100 milligrams", "lasix 100 milligrams", "furosemide 100 mg", "lasix 100 mg", "100 milligrams of furosemide", "100 milligrams of lasix", "100 mg of furosemide", "100 mg of lasix", "furosemide 120", "lasix 120", "120 of furosemide", "120 of lasix", "furosemide 160", "lasix 160", "160 of furosemide", "160 of lasix", "double the home dose of furosemide", "double the home dose of lasix", "double the home dose", "double the home lasix", "double the home furosemide", "double the home diuretic", "double the home diuretic dose", "twice the home dose", "twice the home dose of lasix", "twice the home dose of furosemide", "twice the home lasix", "twice the home furosemide", "twice the home diuretic", "twice the home diuretic dose", "one to two times the home dose", "1 to 2 times the home dose", "one to two times the home dose of lasix", "1 to 2 times the home dose of lasix", "one to two times the home dose of furosemide", "1 to 2 times the home dose of furosemide", "one to two times the home lasix", "1 to 2 times the home lasix", "one to two times the home furosemide", "1 to 2 times the home furosemide", "one to two times the home diuretic", "1 to 2 times the home diuretic", "one to two times the home diuretic dose", "1 to 2 times the home diuretic dose", "one to two and a half times the home dose", "1 to 2 5 times the home dose", "one to two and a half times the home dose of lasix", "1 to 2 5 times the home dose of lasix", "one to two and a half times the home dose of furosemide", "1 to 2 5 times the home dose of furosemide", "one to two and a half times the home lasix", "1 to 2 5 times the home lasix", "one to two and a half times the home furosemide", "1 to 2 5 times the home furosemide", "one to two and a half times the home diuretic", "1 to 2 5 times the home diuretic", "one to two and a half times the home diuretic dose", "1 to 2 5 times the home diuretic dose", "furosemide drip", "lasix drip", "furosemide infusion", "lasix infusion", "furosemide gtt", "lasix gtt", "furosemide for pulmonary edema", "lasix for pulmonary edema", "furosemide for the pulmonary edema", "lasix for the pulmonary edema", "furosemide for chf", "lasix for chf", "furosemide for the chf", "lasix for the chf", "furosemide for heart failure", "lasix for heart failure", "furosemide for the heart failure", "lasix for the heart failure", "furosemide for volume overload", "lasix for volume overload", "furosemide for the volume overload", "lasix for the volume overload", "furosemide for fluid overload", "lasix for fluid overload", "furosemide for the fluid overload", "lasix for the fluid overload", "furosemide for the edema", "lasix for the edema", "furosemide for edema", "lasix for edema", "furosemide for the swelling", "lasix for the swelling", "furosemide for swelling", "lasix for swelling", "furosemide for hyperkalemia", "lasix for hyperkalemia", "furosemide for the hyperkalemia", "lasix for the hyperkalemia", "furosemide for the potassium", "lasix for the potassium", "furosemide for hypercalcemia", "lasix for hypercalcemia", "furosemide for the hypercalcemia", "lasix for the hypercalcemia", "furosemide for the calcium", "lasix for the calcium", "another dose of furosemide", "another dose of lasix", "another furosemide", "another lasix", "repeat furosemide", "repeat lasix", "repeat the furosemide", "repeat the lasix", "second dose of furosemide", "second dose of lasix", "second furosemide", "second lasix", "more furosemide", "more lasix", "furosemide again", "lasix again", "furosemide one more time", "lasix one more time", "one more furosemide", "one more lasix", "give furosemide", "give lasix", "furosemide please", "lasix please", "furosemide stat", "lasix stat", "furosemide now", "lasix now", "some furosemide", "some lasix", "a dose of furosemide", "a dose of lasix", "dose of furosemide", "dose of lasix")
for p in ["bumetanide", "bumex", "torsemide", "demadex", "chlorothiazide", "diuril", "metolazone", "zaroxolyn", "hydrochlorothiazide", "hctz", "spironolactone", "aldactone", "acetazolamide", "diamox", "mannitol for diuresis"]:
    unavailable(p, "Not in the catalog. The diuretic available is furosemide.")
alias("hypertonic_saline_25_bolus", "hypertonic saline bolus", "hypertonic bolus", "23 4", "23 4 percent", "23 4 percent saline", "23 4 saline", "twenty three percent saline", "twenty three point four", "twenty three point four percent", "twenty three point four percent saline", "23 percent saline", "23 percent", "twenty three percent", "hypertonic saline 23 4", "hypertonic saline 23 4 percent", "hypertonic 23 4", "hypertonic 23 4 percent", "23 4 percent hypertonic saline", "23 4 hypertonic saline", "23 4 percent hypertonic", "23 4 hypertonic", "30 cc of 23 4", "30 ml of 23 4", "30 of 23 4", "30 cc of 23 4 percent", "30 ml of 23 4 percent", "30 of 23 4 percent", "30 cc of 23 4 percent saline", "30 ml of 23 4 percent saline", "30 of 23 4 percent saline", "30 cc of hypertonic saline", "30 ml of hypertonic saline", "30 of hypertonic saline", "30 cc of hypertonic", "30 ml of hypertonic", "30 of hypertonic", "30 cc hypertonic saline", "30 ml hypertonic saline", "30 hypertonic saline", "30 cc hypertonic", "30 ml hypertonic", "30 hypertonic", "hypertonic saline 30 cc", "hypertonic saline 30 ml", "hypertonic saline 30", "hypertonic 30 cc", "hypertonic 30 ml", "hypertonic 30", "concentrated saline", "concentrated hypertonic saline", "concentrated hypertonic", "high concentration saline", "high concentration hypertonic saline", "high concentration hypertonic", "25 percent saline", "25 percent hypertonic saline", "25 percent hypertonic", "hypertonic saline 25 percent", "hypertonic 25 percent", "hypertonic saline 25", "hypertonic 25", "25 saline", "25 hypertonic saline", "25 hypertonic", "hypertonic saline push", "hypertonic push", "push hypertonic saline", "push hypertonic", "push 23 4", "push 23 4 percent", "push 23 4 percent saline", "push 23 4 saline", "push twenty three percent", "push twenty three point four", "push twenty three point four percent", "hypertonic saline for herniation", "hypertonic for herniation", "hypertonic saline for the herniation", "hypertonic for the herniation", "hypertonic saline for impending herniation", "hypertonic for impending herniation", "hypertonic saline for the impending herniation", "hypertonic for the impending herniation", "hypertonic saline for the blown pupil", "hypertonic for the blown pupil", "hypertonic saline for blown pupil", "hypertonic for blown pupil", "hypertonic saline for the icp", "hypertonic for the icp", "hypertonic saline for icp", "hypertonic for icp", "hypertonic saline for elevated icp", "hypertonic for elevated icp", "hypertonic saline for the elevated icp", "hypertonic for the elevated icp", "hypertonic saline for raised icp", "hypertonic for raised icp", "hypertonic saline for the raised icp", "hypertonic for the raised icp", "hypertonic saline for increased icp", "hypertonic for increased icp", "hypertonic saline for the increased icp", "hypertonic for the increased icp", "hypertonic saline for intracranial pressure", "hypertonic for intracranial pressure", "hypertonic saline for the intracranial pressure", "hypertonic for the intracranial pressure", "hypertonic saline for elevated intracranial pressure", "hypertonic for elevated intracranial pressure", "hypertonic saline for the elevated intracranial pressure", "hypertonic for the elevated intracranial pressure", "hypertonic saline for raised intracranial pressure", "hypertonic for raised intracranial pressure", "hypertonic saline for the raised intracranial pressure", "hypertonic for the raised intracranial pressure", "hypertonic saline for increased intracranial pressure", "hypertonic for increased intracranial pressure", "hypertonic saline for the increased intracranial pressure", "hypertonic for the increased intracranial pressure", "hypertonic saline for cerebral edema", "hypertonic for cerebral edema", "hypertonic saline for the cerebral edema", "hypertonic for the cerebral edema", "hypertonic saline for brain swelling", "hypertonic for brain swelling", "hypertonic saline for the brain swelling", "hypertonic for the brain swelling", "hypertonic saline for the brain", "hypertonic for the brain", "hypertonic saline for the head", "hypertonic for the head", "hypertonic saline for the head bleed", "hypertonic for the head bleed", "hypertonic saline for head bleed", "hypertonic for head bleed", "hypertonic saline for the bleed", "hypertonic for the bleed", "hypertonic saline for the hemorrhage", "hypertonic for the hemorrhage", "hypertonic saline for the ich", "hypertonic for the ich", "hypertonic saline for ich", "hypertonic for ich", "hypertonic saline for the sah", "hypertonic for the sah", "hypertonic saline for sah", "hypertonic for sah", "hypertonic saline for the sdh", "hypertonic for the sdh", "hypertonic saline for sdh", "hypertonic for sdh", "hypertonic saline for the edh", "hypertonic for the edh", "hypertonic saline for edh", "hypertonic for edh", "hypertonic saline for the tbi", "hypertonic for the tbi", "hypertonic saline for tbi", "hypertonic for tbi", "hypertonic saline for the head injury", "hypertonic for the head injury", "hypertonic saline for head injury", "hypertonic for head injury", "hypertonic saline for the mass", "hypertonic for the mass", "hypertonic saline for the tumor", "hypertonic for the tumor", "hypertonic saline for the midline shift", "hypertonic for the midline shift", "hypertonic saline for midline shift", "hypertonic for midline shift", "hypertonic saline for the shift", "hypertonic for the shift", "hypertonic saline for the stroke", "hypertonic for the stroke", "hypertonic saline for stroke", "hypertonic for stroke", "hypertonic saline for the malignant stroke", "hypertonic for the malignant stroke", "hypertonic saline for malignant stroke", "hypertonic for malignant stroke", "hypertonic saline for the malignant mca", "hypertonic for the malignant mca", "hypertonic saline for malignant mca", "hypertonic for malignant mca", "hypertonic saline for the hydrocephalus", "hypertonic for the hydrocephalus", "hypertonic saline for hydrocephalus", "hypertonic for hydrocephalus", "osmotic therapy bolus", "osmotherapy bolus", "hyperosmolar therapy bolus", "hyperosmolar bolus", "osmotic bolus")
alias("hypertonic_saline_3_infusion", "3 percent", "3 percent saline", "three percent", "three percent saline", "3 percent hypertonic", "three percent hypertonic", "3 percent hypertonic saline", "three percent hypertonic saline", "hypertonic saline 3 percent", "hypertonic saline three percent", "hypertonic 3 percent", "hypertonic three percent", "hypertonic saline 3", "hypertonic 3", "3 saline", "3 hypertonic saline", "3 hypertonic", "hypertonic saline infusion", "hypertonic infusion", "hypertonic saline drip", "hypertonic drip", "hypertonic saline gtt", "hypertonic gtt", "3 percent infusion", "three percent infusion", "3 percent drip", "three percent drip", "3 percent gtt", "three percent gtt", "3 percent saline infusion", "three percent saline infusion", "3 percent saline drip", "three percent saline drip", "3 percent saline gtt", "three percent saline gtt", "hypertonic saline at 30", "hypertonic at 30", "hypertonic saline at 50", "hypertonic at 50", "hypertonic saline at 75", "hypertonic at 75", "hypertonic saline at 100", "hypertonic at 100", "3 percent at 30", "three percent at 30", "3 percent at 50", "three percent at 50", "3 percent at 75", "three percent at 75", "3 percent at 100", "three percent at 100", "3 percent saline at 30", "three percent saline at 30", "3 percent saline at 50", "three percent saline at 50", "3 percent saline at 75", "three percent saline at 75", "3 percent saline at 100", "three percent saline at 100", "100 cc of 3 percent", "100 ml of 3 percent", "100 of 3 percent", "100 cc of three percent", "100 ml of three percent", "100 of three percent", "100 cc of 3 percent saline", "100 ml of 3 percent saline", "100 of 3 percent saline", "100 cc of three percent saline", "100 ml of three percent saline", "100 of three percent saline", "150 cc of 3 percent", "150 ml of 3 percent", "150 of 3 percent", "150 cc of three percent", "150 ml of three percent", "150 of three percent", "150 cc of 3 percent saline", "150 ml of 3 percent saline", "150 of 3 percent saline", "150 cc of three percent saline", "150 ml of three percent saline", "150 of three percent saline", "250 cc of 3 percent", "250 ml of 3 percent", "250 of 3 percent", "250 cc of three percent", "250 ml of three percent", "250 of three percent", "250 cc of 3 percent saline", "250 ml of 3 percent saline", "250 of 3 percent saline", "250 cc of three percent saline", "250 ml of three percent saline", "250 of three percent saline", "3 percent bolus", "three percent bolus", "3 percent saline bolus", "three percent saline bolus", "bolus of 3 percent", "bolus of three percent", "bolus of 3 percent saline", "bolus of three percent saline", "hypertonic saline for hyponatremia", "hypertonic for hyponatremia", "hypertonic saline for the hyponatremia", "hypertonic for the hyponatremia", "hypertonic saline for the sodium", "hypertonic for the sodium", "hypertonic saline for low sodium", "hypertonic for low sodium", "hypertonic saline for the low sodium", "hypertonic for the low sodium", "hypertonic saline for seizure", "hypertonic for seizure", "hypertonic saline for the seizure", "hypertonic for the seizure", "hypertonic saline for seizures", "hypertonic for seizures", "hypertonic saline for the seizures", "hypertonic for the seizures", "hypertonic saline for hyponatremic seizure", "hypertonic for hyponatremic seizure", "hypertonic saline for the hyponatremic seizure", "hypertonic for the hyponatremic seizure", "hypertonic saline for hyponatremic seizures", "hypertonic for hyponatremic seizures", "hypertonic saline for the hyponatremic seizures", "hypertonic for the hyponatremic seizures", "3 percent for hyponatremia", "three percent for hyponatremia", "3 percent for the hyponatremia", "three percent for the hyponatremia", "3 percent for the sodium", "three percent for the sodium", "3 percent for seizure", "three percent for seizure", "3 percent for the seizure", "three percent for the seizure", "3 percent for seizures", "three percent for seizures", "3 percent for the seizures", "three percent for the seizures", "start hypertonic saline", "start hypertonic", "start 3 percent", "start three percent", "start 3 percent saline", "start three percent saline", "hang hypertonic saline", "hang hypertonic", "hang 3 percent", "hang three percent", "hang 3 percent saline", "hang three percent saline", "start a hypertonic saline drip", "start a hypertonic drip", "start a 3 percent drip", "start a three percent drip", "start a hypertonic saline infusion", "start a hypertonic infusion", "start a 3 percent infusion", "start a three percent infusion", "osmotic therapy", "osmotherapy", "hyperosmolar therapy", "raise the sodium", "raise the serum sodium", "bring up the sodium", "bring up the serum sodium", "correct the sodium", "correct the hyponatremia", "correct hyponatremia", "correct the serum sodium", "increase the sodium", "increase the serum sodium")
for p in ["hypertonic saline", "hypertonic", "hypertonic saline bolus", "hypertonic bolus", "hypertonic saline push", "hypertonic push", "push hypertonic saline", "push hypertonic", "osmotic therapy", "osmotherapy", "hyperosmolar therapy", "osmotic therapy bolus", "osmotherapy bolus", "hyperosmolar therapy bolus", "hyperosmolar bolus", "osmotic bolus", "some hypertonic saline", "some hypertonic", "give hypertonic saline", "give hypertonic", "hypertonic saline please", "hypertonic please", "hypertonic saline stat", "hypertonic stat", "hypertonic saline now", "hypertonic now"]:
    for cid in ("hypertonic_saline_25_bolus", "hypertonic_saline_3_infusion"):
        if p in A[cid]: A[cid].remove(p)
    ambiguous(p, "hypertonic_saline_25_bolus", "hypertonic_saline_3_infusion", "mannitol_bolus")
alias("insulin_bolus", "insulin bolus", "insulin push", "iv insulin push", "regular insulin push", "regular insulin bolus", "iv regular insulin", "iv insulin bolus", "10 units of insulin", "ten units of insulin", "10 of insulin", "ten of insulin", "insulin 10", "insulin 10 units", "insulin ten units", "10 units of regular insulin", "ten units of regular insulin", "10 of regular insulin", "ten of regular insulin", "regular insulin 10", "regular insulin 10 units", "regular insulin ten units", "10 units regular insulin", "ten units regular insulin", "10 units iv insulin", "ten units iv insulin", "10 units of iv insulin", "ten units of iv insulin", "10 units insulin iv", "ten units insulin iv", "10 units of insulin iv", "ten units of insulin iv", "insulin 10 units iv", "insulin ten units iv", "10 units regular insulin iv", "ten units regular insulin iv", "10 units of regular insulin iv", "ten units of regular insulin iv", "regular insulin 10 units iv", "regular insulin ten units iv", "5 units of insulin", "five units of insulin", "5 of insulin", "five of insulin", "insulin 5", "insulin 5 units", "insulin five units", "5 units of regular insulin", "five units of regular insulin", "5 of regular insulin", "five of regular insulin", "regular insulin 5", "regular insulin 5 units", "regular insulin five units", "0 1 per kilo insulin", "0 1 per kilo insulin bolus", "insulin 0 1 per kilo", "insulin 0 1 per kilo bolus", "0 1 units per kilo insulin", "0 1 units per kilo insulin bolus", "insulin 0 1 units per kilo", "insulin 0 1 units per kilo bolus", "0 1 per kilo regular insulin", "0 1 per kilo regular insulin bolus", "regular insulin 0 1 per kilo", "regular insulin 0 1 per kilo bolus", "0 1 units per kilo regular insulin", "0 1 units per kilo regular insulin bolus", "regular insulin 0 1 units per kilo", "regular insulin 0 1 units per kilo bolus", "insulin for hyperkalemia", "insulin for the hyperkalemia", "insulin for the potassium", "insulin for potassium", "insulin for k", "insulin for the k", "insulin for high potassium", "insulin for the high potassium", "insulin for high k", "insulin for the high k", "insulin and glucose for hyperkalemia", "insulin and dextrose for hyperkalemia", "insulin and d50 for hyperkalemia", "insulin with dextrose for hyperkalemia", "insulin with glucose for hyperkalemia", "insulin with d50 for hyperkalemia", "insulin and glucose for the hyperkalemia", "insulin and dextrose for the hyperkalemia", "insulin and d50 for the hyperkalemia", "insulin with dextrose for the hyperkalemia", "insulin with glucose for the hyperkalemia", "insulin with d50 for the hyperkalemia", "insulin and glucose for the potassium", "insulin and dextrose for the potassium", "insulin and d50 for the potassium", "insulin with dextrose for the potassium", "insulin with glucose for the potassium", "insulin with d50 for the potassium", "insulin and glucose for potassium", "insulin and dextrose for potassium", "insulin and d50 for potassium", "insulin with dextrose for potassium", "insulin with glucose for potassium", "insulin with d50 for potassium", "insulin with dextrose", "insulin with glucose", "insulin with d50", "shift the potassium", "shift the k", "shift potassium", "shift k", "shift the potassium intracellularly", "shift potassium intracellularly", "shift the k intracellularly", "shift k intracellularly", "drive the potassium into the cells", "drive potassium into the cells", "drive the k into the cells", "drive k into the cells", "push the potassium into the cells", "push potassium into the cells", "push the k into the cells", "push k into the cells", "move the potassium into the cells", "move potassium into the cells", "move the k into the cells", "move k into the cells", "intracellular shift", "intracellular potassium shift", "intracellular k shift", "potassium shift", "k shift", "temporize the hyperkalemia", "temporize hyperkalemia", "temporise the hyperkalemia", "temporise hyperkalemia", "temporize the k", "temporize k", "temporise the k", "temporise k")
for p in ["insulin with dextrose", "insulin with glucose", "insulin with d50"]:
    A["insulin_bolus"].remove(p); expand(p, "insulin_bolus", "d50_bolus")
for p in ["shift the potassium", "shift the k", "shift potassium", "shift k", "shift the potassium intracellularly", "shift potassium intracellularly", "shift the k intracellularly", "shift k intracellularly", "drive the potassium into the cells", "drive potassium into the cells", "drive the k into the cells", "drive k into the cells", "push the potassium into the cells", "push potassium into the cells", "push the k into the cells", "push k into the cells", "move the potassium into the cells", "move potassium into the cells", "move the k into the cells", "move k into the cells", "intracellular shift", "intracellular potassium shift", "intracellular k shift", "potassium shift", "k shift", "temporize the hyperkalemia", "temporize hyperkalemia", "temporise the hyperkalemia", "temporise hyperkalemia", "temporize the k", "temporize k", "temporise the k", "temporise k"]:
    A["insulin_bolus"].remove(p); unavailable(p, "Name the drugs. The parser does not expand a diagnosis into its treatment.")
alias("insulin_drip", "insulin drip", "insulin infusion", "insulin gtt", "iv insulin drip", "iv insulin infusion", "regular insulin drip", "regular insulin infusion", "regular insulin gtt", "insulin at 0 1", "insulin at 0 1 per kilo", "insulin at 0 1 per kilo per hour", "insulin at 0 1 units per kilo per hour", "insulin 0 1 per kilo per hour", "insulin 0 1 units per kilo per hour", "0 1 per kilo per hour insulin", "0 1 units per kilo per hour insulin", "0 1 per kilo per hour of insulin", "0 1 units per kilo per hour of insulin", "insulin drip at 0 1", "insulin drip at 0 1 per kilo", "insulin drip at 0 1 per kilo per hour", "insulin drip at 0 1 units per kilo per hour", "insulin infusion at 0 1", "insulin infusion at 0 1 per kilo", "insulin infusion at 0 1 per kilo per hour", "insulin infusion at 0 1 units per kilo per hour", "insulin at 0 05", "insulin at 0 05 per kilo", "insulin at 0 05 per kilo per hour", "insulin at 0 05 units per kilo per hour", "insulin 0 05 per kilo per hour", "insulin 0 05 units per kilo per hour", "0 05 per kilo per hour insulin", "0 05 units per kilo per hour insulin", "insulin drip at 0 05", "insulin drip at 0 05 per kilo", "insulin infusion at 0 05", "insulin infusion at 0 05 per kilo", "insulin at 5", "insulin at 5 units", "insulin at 5 an hour", "insulin at 5 units an hour", "insulin at 5 units per hour", "insulin 5 an hour", "insulin 5 units an hour", "insulin 5 units per hour", "insulin drip at 5", "insulin drip at 5 an hour", "insulin drip at 5 units an hour", "insulin drip at 5 units per hour", "insulin infusion at 5", "insulin infusion at 5 an hour", "insulin infusion at 5 units an hour", "insulin infusion at 5 units per hour", "insulin at 7", "insulin at 7 units", "insulin at 7 an hour", "insulin at 7 units an hour", "insulin at 10", "insulin at 10 units", "insulin at 10 an hour", "insulin at 10 units an hour", "insulin at 10 units per hour", "insulin 10 an hour", "insulin 10 units an hour", "insulin 10 units per hour", "insulin drip at 10", "insulin drip at 10 an hour", "insulin drip at 10 units an hour", "insulin drip at 10 units per hour", "insulin infusion at 10", "insulin infusion at 10 an hour", "insulin infusion at 10 units an hour", "insulin infusion at 10 units per hour", "start an insulin drip", "start an insulin infusion", "start insulin drip", "start insulin infusion", "start the insulin drip", "start the insulin infusion", "hang an insulin drip", "hang an insulin infusion", "hang insulin", "hang the insulin", "hang insulin drip", "hang insulin infusion", "continuous insulin", "insulin continuous", "continuous insulin infusion", "continuous insulin drip", "insulin per protocol", "insulin protocol", "dka protocol", "dka insulin protocol", "insulin per dka protocol", "insulin drip per protocol", "insulin infusion per protocol", "insulin drip per dka protocol", "insulin infusion per dka protocol", "dka drip", "dka insulin drip", "dka insulin infusion", "insulin for dka", "insulin drip for dka", "insulin infusion for dka", "insulin for the dka", "insulin drip for the dka", "insulin infusion for the dka", "insulin for hhs", "insulin drip for hhs", "insulin infusion for hhs", "insulin for the hhs", "insulin drip for the hhs", "insulin infusion for the hhs", "insulin for hyperglycemia", "insulin drip for hyperglycemia", "insulin infusion for hyperglycemia", "insulin for the hyperglycemia", "insulin drip for the hyperglycemia", "insulin infusion for the hyperglycemia", "insulin for the sugar", "insulin drip for the sugar", "insulin infusion for the sugar", "insulin for the glucose", "insulin drip for the glucose", "insulin infusion for the glucose", "insulin for the high sugar", "insulin drip for the high sugar", "insulin infusion for the high sugar", "insulin for the high glucose", "insulin drip for the high glucose", "insulin infusion for the high glucose", "high dose insulin drip", "high dose insulin infusion", "high dose insulin", "hdi", "high dose insulin euglycemia", "high dose insulin euglycemic therapy", "hie", "hiet", "insulin for ccb overdose", "insulin for the ccb overdose", "insulin for calcium channel blocker overdose", "insulin for the calcium channel blocker overdose", "insulin for beta blocker overdose", "insulin for the beta blocker overdose", "insulin drip for ccb overdose", "insulin drip for the ccb overdose", "insulin drip for calcium channel blocker overdose", "insulin drip for the calcium channel blocker overdose", "insulin drip for beta blocker overdose", "insulin drip for the beta blocker overdose", "insulin infusion for ccb overdose", "insulin infusion for the ccb overdose", "insulin infusion for calcium channel blocker overdose", "insulin infusion for the calcium channel blocker overdose", "insulin infusion for beta blocker overdose", "insulin infusion for the beta blocker overdose", "1 unit per kilo insulin", "1 unit per kilo insulin drip", "1 unit per kilo insulin infusion", "insulin 1 unit per kilo", "insulin drip 1 unit per kilo", "insulin infusion 1 unit per kilo", "insulin at 1 unit per kilo", "insulin drip at 1 unit per kilo", "insulin infusion at 1 unit per kilo", "insulin at 1 unit per kilo per hour", "insulin drip at 1 unit per kilo per hour", "insulin infusion at 1 unit per kilo per hour", "1 unit per kilo per hour insulin", "1 unit per kilo per hour insulin drip", "1 unit per kilo per hour insulin infusion", "1 per kilo insulin", "1 per kilo insulin drip", "1 per kilo insulin infusion", "insulin 1 per kilo", "insulin drip 1 per kilo", "insulin infusion 1 per kilo", "insulin at 1 per kilo", "insulin drip at 1 per kilo", "insulin infusion at 1 per kilo", "insulin at 1 per kilo per hour", "insulin drip at 1 per kilo per hour", "insulin infusion at 1 per kilo per hour", "1 per kilo per hour insulin", "1 per kilo per hour insulin drip", "1 per kilo per hour insulin infusion")
for p in ["high dose insulin drip", "high dose insulin infusion", "high dose insulin", "hdi", "high dose insulin euglycemia", "high dose insulin euglycemic therapy", "hie", "hiet"]:
    if p in A["insulin_drip"]: A["insulin_drip"].remove(p)
    UNAVAIL.pop(p, None); alias("insulin_drip", p)
for p in ["insulin", "regular insulin", "iv insulin", "humulin", "novolin", "humulin r", "novolin r", "some insulin", "give insulin", "insulin please", "insulin stat", "insulin now", "regular", "insulin regular"]:
    ambiguous(p, "insulin_bolus", "insulin_drip")
for p in ["lantus", "glargine", "levemir", "detemir", "nph", "lispro", "humalog", "aspart", "novolog", "glulisine", "apidra", "subq insulin", "subcutaneous insulin", "sliding scale", "sliding scale insulin", "basal insulin", "long acting insulin", "rapid acting insulin", "insulin pen", "metformin", "glucophage", "glipizide", "glyburide", "sulfonylurea", "empagliflozin", "jardiance", "dapagliflozin", "farxiga", "sglt2", "sglt2 inhibitor", "liraglutide", "victoza", "semaglutide", "ozempic", "wegovy", "glp1", "glp 1", "sitagliptin", "januvia", "pioglitazone", "actos"]:
    unavailable(p, "Not in the catalog. Insulin here is the IV regular insulin bolus and the drip.")
alias("levetiracetam_bolus", "levetiracetam", "keppra", "iv levetiracetam", "iv keppra", "keppra load", "levetiracetam load", "load keppra", "load levetiracetam", "load with keppra", "load with levetiracetam", "keppra loading dose", "levetiracetam loading dose", "loading dose of keppra", "loading dose of levetiracetam", "keppra bolus", "levetiracetam bolus", "keppra push", "levetiracetam push", "keppra 1 gram", "levetiracetam 1 gram", "keppra 1 5 grams", "levetiracetam 1 5 grams", "keppra 2 grams", "levetiracetam 2 grams", "keppra 3 grams", "levetiracetam 3 grams", "keppra 60 per kilo", "levetiracetam 60 per kilo", "keppra 40 per kilo", "levetiracetam 40 per kilo", "keppra 20 per kilo", "levetiracetam 20 per kilo", "60 per kilo keppra", "60 per kilo levetiracetam", "40 per kilo keppra", "40 per kilo levetiracetam", "20 per kilo keppra", "20 per kilo levetiracetam", "a gram of keppra", "a gram of levetiracetam", "gram of keppra", "gram of levetiracetam", "1 gram of keppra", "1 gram of levetiracetam", "one gram of keppra", "one gram of levetiracetam", "2 grams of keppra", "2 grams of levetiracetam", "two grams of keppra", "two grams of levetiracetam", "3 grams of keppra", "3 grams of levetiracetam", "three grams of keppra", "three grams of levetiracetam", "1 5 grams of keppra", "1 5 grams of levetiracetam", "keppra for seizure", "levetiracetam for seizure", "keppra for the seizure", "levetiracetam for the seizure", "keppra for seizures", "levetiracetam for seizures", "keppra for the seizures", "levetiracetam for the seizures", "keppra for status", "levetiracetam for status", "keppra for the status", "levetiracetam for the status", "keppra for status epilepticus", "levetiracetam for status epilepticus", "keppra for the status epilepticus", "levetiracetam for the status epilepticus", "keppra for seizure prophylaxis", "levetiracetam for seizure prophylaxis", "keppra prophylaxis", "levetiracetam prophylaxis", "prophylactic keppra", "prophylactic levetiracetam", "keppra for the head bleed", "levetiracetam for the head bleed", "keppra for head bleed", "levetiracetam for head bleed", "keppra for the tbi", "levetiracetam for the tbi", "keppra for tbi", "levetiracetam for tbi", "second line antiepileptic", "second line anticonvulsant", "second line aed", "second line seizure medication", "second line seizure med", "second line for seizure", "second line for the seizure", "second line for seizures", "second line for the seizures", "second line for status", "second line for the status", "second line agent", "second line agent for seizure", "second line agent for the seizure", "second line agent for status", "second line agent for the status")
for p in ["second line antiepileptic", "second line anticonvulsant", "second line aed", "second line seizure medication", "second line seizure med", "second line for seizure", "second line for the seizure", "second line for seizures", "second line for the seizures", "second line for status", "second line for the status", "second line agent", "second line agent for seizure", "second line agent for the seizure", "second line agent for status", "second line agent for the status"]:
    A["levetiracetam_bolus"].remove(p); ambiguous(p, "levetiracetam_bolus", "fos_phenytoin")
alias("fos_phenytoin", "fosphenytoin", "fos phenytoin", "cerebyx", "phenytoin", "dilantin", "iv fosphenytoin", "iv phenytoin", "iv cerebyx", "iv dilantin", "fosphenytoin load", "phenytoin load", "cerebyx load", "dilantin load", "load fosphenytoin", "load phenytoin", "load cerebyx", "load dilantin", "load with fosphenytoin", "load with phenytoin", "load with cerebyx", "load with dilantin", "fosphenytoin loading dose", "phenytoin loading dose", "cerebyx loading dose", "dilantin loading dose", "loading dose of fosphenytoin", "loading dose of phenytoin", "loading dose of cerebyx", "loading dose of dilantin", "fosphenytoin 20 per kilo", "phenytoin 20 per kilo", "cerebyx 20 per kilo", "dilantin 20 per kilo", "20 per kilo fosphenytoin", "20 per kilo phenytoin", "20 per kilo cerebyx", "20 per kilo dilantin", "fosphenytoin 20 pe per kilo", "cerebyx 20 pe per kilo", "phenytoin equivalents", "fosphenytoin 1 gram", "phenytoin 1 gram", "cerebyx 1 gram", "dilantin 1 gram", "a gram of fosphenytoin", "a gram of phenytoin", "a gram of cerebyx", "a gram of dilantin", "gram of fosphenytoin", "gram of phenytoin", "gram of cerebyx", "gram of dilantin", "1 gram of fosphenytoin", "1 gram of phenytoin", "1 gram of cerebyx", "1 gram of dilantin", "one gram of fosphenytoin", "one gram of phenytoin", "one gram of cerebyx", "one gram of dilantin", "fosphenytoin 1500", "phenytoin 1500", "cerebyx 1500", "dilantin 1500", "1500 of fosphenytoin", "1500 of phenytoin", "1500 of cerebyx", "1500 of dilantin", "fosphenytoin 1500 pe", "cerebyx 1500 pe", "fosphenytoin for seizure", "phenytoin for seizure", "cerebyx for seizure", "dilantin for seizure", "fosphenytoin for the seizure", "phenytoin for the seizure", "cerebyx for the seizure", "dilantin for the seizure", "fosphenytoin for seizures", "phenytoin for seizures", "cerebyx for seizures", "dilantin for seizures", "fosphenytoin for the seizures", "phenytoin for the seizures", "cerebyx for the seizures", "dilantin for the seizures", "fosphenytoin for status", "phenytoin for status", "cerebyx for status", "dilantin for status", "fosphenytoin for the status", "phenytoin for the status", "cerebyx for the status", "dilantin for the status", "fosphenytoin for status epilepticus", "phenytoin for status epilepticus", "cerebyx for status epilepticus", "dilantin for status epilepticus", "fosphenytoin for the status epilepticus", "phenytoin for the status epilepticus", "cerebyx for the status epilepticus", "dilantin for the status epilepticus")
for p in ["valproate", "valproic acid", "depakote", "depacon", "lacosamide", "vimpat", "phenobarbital", "phenobarb", "luminal", "topiramate", "topamax", "carbamazepine", "tegretol", "oxcarbazepine", "trileptal", "lamotrigine", "lamictal", "clobazam", "onfi", "brivaracetam", "briviact", "zonisamide", "zonegran", "gabapentin", "neurontin", "pregabalin", "lyrica"]:
    unavailable(p, "Not in the catalog. Antiepileptics available: lorazepam, midazolam, levetiracetam, fosphenytoin, propofol.")
for p in ["antiepileptic", "anticonvulsant", "aed", "antiepileptics", "anticonvulsants", "aeds", "seizure medication", "seizure meds", "seizure med", "seizure medicine", "something for the seizure", "something for seizure", "something for seizures", "something for the seizures", "stop the seizure", "stop the seizures", "break the seizure", "break the seizures", "abort the seizure", "abort the seizures", "treat the seizure", "treat the seizures", "treat seizure", "treat seizures", "treat status", "treat the status", "treat status epilepticus", "treat the status epilepticus", "seizure control", "control the seizure", "control the seizures", "control seizure", "control seizures", "first line for seizure", "first line for the seizure", "first line for seizures", "first line for the seizures", "first line for status", "first line for the status", "first line antiepileptic", "first line anticonvulsant", "first line aed", "first line seizure medication", "first line seizure med", "first line agent", "first line agent for seizure", "first line agent for the seizure", "first line agent for status", "first line agent for the status"]:
    ambiguous(p, "lorazepam_bolus", "midazolam_bolus", "levetiracetam_bolus", "fos_phenytoin", "propofol_infusion")
alias("mannitol_bolus", "mannitol", "mannitol bolus", "iv mannitol", "mannitol push", "push mannitol", "osmitrol", "mannitol 1 per kilo", "mannitol 1 gram per kilo", "mannitol 0 5 per kilo", "mannitol 0 5 grams per kilo", "mannitol 0 25 per kilo", "mannitol 0 25 grams per kilo", "mannitol 1 5 per kilo", "mannitol 1 5 grams per kilo", "mannitol 2 per kilo", "mannitol 2 grams per kilo", "1 per kilo mannitol", "1 gram per kilo mannitol", "0 5 per kilo mannitol", "0 5 grams per kilo mannitol", "0 25 per kilo mannitol", "0 25 grams per kilo mannitol", "1 5 per kilo mannitol", "1 5 grams per kilo mannitol", "2 per kilo mannitol", "2 grams per kilo mannitol", "mannitol 100 grams", "mannitol 100", "100 grams of mannitol", "100 of mannitol", "mannitol 50 grams", "mannitol 50", "50 grams of mannitol", "50 of mannitol", "mannitol 75 grams", "mannitol 75", "75 grams of mannitol", "75 of mannitol", "mannitol 20 percent", "20 percent mannitol", "mannitol 25 percent", "25 percent mannitol", "mannitol for herniation", "mannitol for the herniation", "mannitol for impending herniation", "mannitol for the impending herniation", "mannitol for the blown pupil", "mannitol for blown pupil", "mannitol for the icp", "mannitol for icp", "mannitol for elevated icp", "mannitol for the elevated icp", "mannitol for raised icp", "mannitol for the raised icp", "mannitol for increased icp", "mannitol for the increased icp", "mannitol for intracranial pressure", "mannitol for the intracranial pressure", "mannitol for elevated intracranial pressure", "mannitol for the elevated intracranial pressure", "mannitol for raised intracranial pressure", "mannitol for the raised intracranial pressure", "mannitol for increased intracranial pressure", "mannitol for the increased intracranial pressure", "mannitol for cerebral edema", "mannitol for the cerebral edema", "mannitol for brain swelling", "mannitol for the brain swelling", "mannitol for the brain", "mannitol for the head", "mannitol for the head bleed", "mannitol for head bleed", "mannitol for the bleed", "mannitol for the hemorrhage", "mannitol for the ich", "mannitol for ich", "mannitol for the sah", "mannitol for sah", "mannitol for the sdh", "mannitol for sdh", "mannitol for the edh", "mannitol for edh", "mannitol for the tbi", "mannitol for tbi", "mannitol for the head injury", "mannitol for head injury", "mannitol for the mass", "mannitol for the tumor", "mannitol for the midline shift", "mannitol for midline shift", "mannitol for the shift", "mannitol for the stroke", "mannitol for stroke", "mannitol for the malignant stroke", "mannitol for malignant stroke", "mannitol for the malignant mca", "mannitol for malignant mca", "mannitol for the hydrocephalus", "mannitol for hydrocephalus", "mannitol for glaucoma", "mannitol for the glaucoma", "mannitol for acute angle closure", "mannitol for the acute angle closure", "mannitol for angle closure", "mannitol for the angle closure", "mannitol for the eye", "mannitol for the eye pressure", "mannitol for eye pressure", "mannitol for the iop", "mannitol for iop", "mannitol for elevated iop", "mannitol for the elevated iop", "mannitol for raised iop", "mannitol for the raised iop", "mannitol for increased iop", "mannitol for the increased iop", "mannitol for intraocular pressure", "mannitol for the intraocular pressure", "mannitol for elevated intraocular pressure", "mannitol for the elevated intraocular pressure", "mannitol for raised intraocular pressure", "mannitol for the raised intraocular pressure", "mannitol for increased intraocular pressure", "mannitol for the increased intraocular pressure", "osmotic diuretic", "an osmotic diuretic", "osmotic diuresis", "osmotic diuretic bolus", "osmotic diuretic push")
alias("potassium_chloride_kcl", "potassium chloride", "kcl", "k cl", "potassium", "k", "iv potassium", "iv kcl", "iv k", "po potassium", "po kcl", "po k", "oral potassium", "oral kcl", "oral k", "potassium run", "k run", "potassium runs", "k runs", "potassium rider", "k rider", "potassium riders", "k riders", "run of potassium", "run of k", "runs of potassium", "runs of k", "rider of potassium", "rider of k", "riders of potassium", "riders of k", "potassium replacement", "k replacement", "kcl replacement", "replace potassium", "replace k", "replace kcl", "replace the potassium", "replace the k", "replace the kcl", "potassium repletion", "k repletion", "kcl repletion", "replete potassium", "replete k", "replete kcl", "replete the potassium", "replete the k", "replete the kcl", "potassium supplementation", "k supplementation", "kcl supplementation", "supplement potassium", "supplement k", "supplement kcl", "supplement the potassium", "supplement the k", "supplement the kcl", "potassium supplement", "k supplement", "kcl supplement", "give potassium", "give k", "give kcl", "some potassium", "some k", "some kcl", "potassium please", "k please", "kcl please", "potassium stat", "k stat", "kcl stat", "potassium now", "k now", "kcl now", "10 of potassium", "10 of k", "10 of kcl", "20 of potassium", "20 of k", "20 of kcl", "40 of potassium", "40 of k", "40 of kcl", "60 of potassium", "60 of k", "60 of kcl", "10 meq of potassium", "10 meq of k", "10 meq of kcl", "20 meq of potassium", "20 meq of k", "20 meq of kcl", "40 meq of potassium", "40 meq of k", "40 meq of kcl", "60 meq of potassium", "60 meq of k", "60 meq of kcl", "potassium 10", "k 10", "kcl 10", "potassium 20", "k 20", "kcl 20", "potassium 40", "k 40", "kcl 40", "potassium 60", "k 60", "kcl 60", "potassium 10 meq", "k 10 meq", "kcl 10 meq", "potassium 20 meq", "k 20 meq", "kcl 20 meq", "potassium 40 meq", "k 40 meq", "kcl 40 meq", "potassium 60 meq", "k 60 meq", "kcl 60 meq", "10 meq potassium", "10 meq k", "10 meq kcl", "20 meq potassium", "20 meq k", "20 meq kcl", "40 meq potassium", "40 meq k", "40 meq kcl", "60 meq potassium", "60 meq k", "60 meq kcl", "potassium for hypokalemia", "k for hypokalemia", "kcl for hypokalemia", "potassium for the hypokalemia", "k for the hypokalemia", "kcl for the hypokalemia", "potassium for the low potassium", "k for the low potassium", "kcl for the low potassium", "potassium for low potassium", "k for low potassium", "kcl for low potassium", "potassium for the low k", "k for the low k", "kcl for the low k", "potassium for low k", "k for low k", "kcl for low k", "potassium for dka", "k for dka", "kcl for dka", "potassium for the dka", "k for the dka", "kcl for the dka", "potassium in the fluids", "k in the fluids", "kcl in the fluids", "potassium in the bag", "k in the bag", "kcl in the bag", "add potassium", "add k", "add kcl", "add potassium to the fluids", "add k to the fluids", "add kcl to the fluids", "add potassium to the bag", "add k to the bag", "add kcl to the bag", "potassium phosphate", "k phos", "kphos", "k phosphate", "potassium phos", "sodium phosphate", "na phos", "naphos", "na phosphate", "sodium phos", "phosphate replacement", "phos replacement", "replace phosphate", "replace phos", "replace the phosphate", "replace the phos", "phosphate repletion", "phos repletion", "replete phosphate", "replete phos", "replete the phosphate", "replete the phos", "iv phosphate", "iv phos", "po phosphate", "po phos", "oral phosphate", "oral phos", "phosphate supplementation", "phos supplementation", "supplement phosphate", "supplement phos", "supplement the phosphate", "supplement the phos", "phosphate supplement", "phos supplement", "give phosphate", "give phos", "some phosphate", "some phos", "phosphate please", "phos please", "phosphate stat", "phos stat", "phosphate now", "phos now", "neutra phos", "neutraphos", "k phos neutral", "phospha soda")
for p in ["potassium phosphate", "k phos", "kphos", "k phosphate", "potassium phos", "sodium phosphate", "na phos", "naphos", "na phosphate", "sodium phos", "phosphate replacement", "phos replacement", "replace phosphate", "replace phos", "replace the phosphate", "replace the phos", "phosphate repletion", "phos repletion", "replete phosphate", "replete phos", "replete the phosphate", "replete the phos", "iv phosphate", "iv phos", "po phosphate", "po phos", "oral phosphate", "oral phos", "phosphate supplementation", "phos supplementation", "supplement phosphate", "supplement phos", "supplement the phosphate", "supplement the phos", "phosphate supplement", "phos supplement", "give phosphate", "give phos", "some phosphate", "some phos", "phosphate please", "phos please", "phosphate stat", "phos stat", "phosphate now", "phos now", "neutra phos", "neutraphos", "k phos neutral", "phospha soda"]:
    A["potassium_chloride_kcl"].remove(p); unavailable(p, "Phosphate replacement is not in the catalog; the phosphate level is.")
for p in ["potassium", "k", "some potassium", "some k", "potassium please", "k please", "potassium stat", "k stat", "potassium now", "k now"]:
    if p in A["potassium_chloride_kcl"]: A["potassium_chloride_kcl"].remove(p)
    ambiguous(p, "potassium_chloride_kcl", "basic_chemistry_chem_7")
alias("potassium_iodide_and_iodine", "potassium iodide", "ski", "sski", "iodine", "iodide", "lugols", "lugols solution", "lugol", "lugol solution", "potassium iodide and iodine", "iodine and potassium iodide", "saturated solution of potassium iodide", "saturated potassium iodide", "iodine for thyroid storm", "iodide for thyroid storm", "ski for thyroid storm", "sski for thyroid storm", "lugols for thyroid storm", "iodine for the thyroid storm", "iodide for the thyroid storm", "ski for the thyroid storm", "sski for the thyroid storm", "lugols for the thyroid storm", "iodine after ptu", "iodide after ptu", "ski after ptu", "sski after ptu", "lugols after ptu", "iodine after the ptu", "iodide after the ptu", "ski after the ptu", "sski after the ptu", "lugols after the ptu", "iodine an hour after ptu", "iodide an hour after ptu", "ski an hour after ptu", "sski an hour after ptu", "lugols an hour after ptu", "iodine an hour after the ptu", "iodide an hour after the ptu", "ski an hour after the ptu", "sski an hour after the ptu", "lugols an hour after the ptu", "iodine one hour after ptu", "iodide one hour after ptu", "ski one hour after ptu", "sski one hour after ptu", "lugols one hour after ptu", "iodine one hour after the ptu", "iodide one hour after the ptu", "ski one hour after the ptu", "sski one hour after the ptu", "lugols one hour after the ptu", "iodine 1 hour after ptu", "iodide 1 hour after ptu", "ski 1 hour after ptu", "sski 1 hour after ptu", "lugols 1 hour after ptu", "iodine 1 hour after the ptu", "iodide 1 hour after the ptu", "ski 1 hour after the ptu", "sski 1 hour after the ptu", "lugols 1 hour after the ptu", "iodine after thionamide", "iodide after thionamide", "ski after thionamide", "sski after thionamide", "lugols after thionamide", "iodine after the thionamide", "iodide after the thionamide", "ski after the thionamide", "sski after the thionamide", "lugols after the thionamide", "iodine after methimazole", "iodide after methimazole", "ski after methimazole", "sski after methimazole", "lugols after methimazole", "iodine after the methimazole", "iodide after the methimazole", "ski after the methimazole", "sski after the methimazole", "lugols after the methimazole", "wolff chaikoff", "wolff chaikoff effect", "block thyroid hormone release", "block hormone release", "block release", "block the release", "block thyroid release", "block the thyroid release", "block release of thyroid hormone", "block the release of thyroid hormone", "inhibit thyroid hormone release", "inhibit hormone release", "inhibit release", "inhibit the release", "inhibit thyroid release", "inhibit the thyroid release", "inhibit release of thyroid hormone", "inhibit the release of thyroid hormone")
alias("propylthiouracil", "propylthiouracil", "ptu", "po ptu", "po propylthiouracil", "oral ptu", "oral propylthiouracil", "ptu by mouth", "propylthiouracil by mouth", "ptu by ng", "propylthiouracil by ng", "ptu via ng", "propylthiouracil via ng", "ptu through the ng", "propylthiouracil through the ng", "ptu down the ng", "propylthiouracil down the ng", "ptu load", "propylthiouracil load", "load ptu", "load propylthiouracil", "load with ptu", "load with propylthiouracil", "ptu loading dose", "propylthiouracil loading dose", "loading dose of ptu", "loading dose of propylthiouracil", "ptu 500", "propylthiouracil 500", "ptu 600", "propylthiouracil 600", "ptu 1000", "propylthiouracil 1000", "500 of ptu", "500 of propylthiouracil", "600 of ptu", "600 of propylthiouracil", "1000 of ptu", "1000 of propylthiouracil", "ptu 500 milligrams", "propylthiouracil 500 milligrams", "ptu 600 milligrams", "propylthiouracil 600 milligrams", "ptu 1000 milligrams", "propylthiouracil 1000 milligrams", "ptu 500 mg", "propylthiouracil 500 mg", "ptu 600 mg", "propylthiouracil 600 mg", "ptu 1000 mg", "propylthiouracil 1000 mg", "500 milligrams of ptu", "500 milligrams of propylthiouracil", "600 milligrams of ptu", "600 milligrams of propylthiouracil", "1000 milligrams of ptu", "1000 milligrams of propylthiouracil", "500 mg of ptu", "500 mg of propylthiouracil", "600 mg of ptu", "600 mg of propylthiouracil", "1000 mg of ptu", "1000 mg of propylthiouracil", "a gram of ptu", "a gram of propylthiouracil", "gram of ptu", "gram of propylthiouracil", "1 gram of ptu", "1 gram of propylthiouracil", "one gram of ptu", "one gram of propylthiouracil", "ptu for thyroid storm", "propylthiouracil for thyroid storm", "ptu for the thyroid storm", "propylthiouracil for the thyroid storm", "ptu for hyperthyroidism", "propylthiouracil for hyperthyroidism", "ptu for the hyperthyroidism", "propylthiouracil for the hyperthyroidism", "ptu for thyrotoxicosis", "propylthiouracil for thyrotoxicosis", "ptu for the thyrotoxicosis", "propylthiouracil for the thyrotoxicosis", "ptu for graves", "propylthiouracil for graves", "ptu for the graves", "propylthiouracil for the graves", "ptu before iodine", "propylthiouracil before iodine", "ptu before the iodine", "propylthiouracil before the iodine", "ptu before iodide", "propylthiouracil before iodide", "ptu before the iodide", "propylthiouracil before the iodide", "ptu before ski", "propylthiouracil before ski", "ptu before the ski", "propylthiouracil before the ski", "ptu before sski", "propylthiouracil before sski", "ptu before the sski", "propylthiouracil before the sski", "ptu before lugols", "propylthiouracil before lugols", "ptu before the lugols", "propylthiouracil before the lugols", "ptu first", "propylthiouracil first", "ptu an hour before iodine", "propylthiouracil an hour before iodine", "ptu an hour before the iodine", "propylthiouracil an hour before the iodine", "ptu one hour before iodine", "propylthiouracil one hour before iodine", "ptu one hour before the iodine", "propylthiouracil one hour before the iodine", "ptu 1 hour before iodine", "propylthiouracil 1 hour before iodine", "ptu 1 hour before the iodine", "propylthiouracil 1 hour before the iodine", "thionamide", "a thionamide", "thionamides", "antithyroid", "antithyroid drug", "antithyroid medication", "antithyroid med", "antithyroid medicine", "antithyroid agent", "antithyroid drugs", "antithyroid medications", "antithyroid meds", "antithyroid medicines", "antithyroid agents", "anti thyroid", "anti thyroid drug", "anti thyroid medication", "anti thyroid med", "anti thyroid medicine", "anti thyroid agent", "anti thyroid drugs", "anti thyroid medications", "anti thyroid meds", "anti thyroid medicines", "anti thyroid agents", "block thyroid hormone synthesis", "block hormone synthesis", "block synthesis", "block the synthesis", "block thyroid synthesis", "block the thyroid synthesis", "block synthesis of thyroid hormone", "block the synthesis of thyroid hormone", "inhibit thyroid hormone synthesis", "inhibit hormone synthesis", "inhibit synthesis", "inhibit the synthesis", "inhibit thyroid synthesis", "inhibit the thyroid synthesis", "inhibit synthesis of thyroid hormone", "inhibit the synthesis of thyroid hormone", "block thyroid hormone production", "block hormone production", "block production", "block the production", "block thyroid production", "block the thyroid production", "block production of thyroid hormone", "block the production of thyroid hormone", "inhibit thyroid hormone production", "inhibit hormone production", "inhibit production", "inhibit the production", "inhibit thyroid production", "inhibit the thyroid production", "inhibit production of thyroid hormone", "inhibit the production of thyroid hormone", "block peripheral conversion", "block the peripheral conversion", "block t4 to t3 conversion", "block the t4 to t3 conversion", "block conversion of t4 to t3", "block the conversion of t4 to t3", "inhibit peripheral conversion", "inhibit the peripheral conversion", "inhibit t4 to t3 conversion", "inhibit the t4 to t3 conversion", "inhibit conversion of t4 to t3", "inhibit the conversion of t4 to t3")
for p in ["methimazole", "tapazole", "carbimazole", "cholestyramine", "questran", "levothyroxine", "synthroid", "t4", "liothyronine", "cytomel", "t3", "iv levothyroxine", "iv t4", "iv synthroid", "iv liothyronine", "iv t3", "iv cytomel", "thyroid hormone", "thyroid replacement", "thyroid hormone replacement", "levothyroxine for myxedema", "t4 for myxedema", "synthroid for myxedema", "levothyroxine for myxedema coma", "t4 for myxedema coma", "synthroid for myxedema coma"]:
    unavailable(p, "Not in the catalog. Thyroid drugs available: propylthiouracil, potassium iodide and iodine, propranolol.")
alias("tdap", "tdap", "t dap", "tetanus", "tetanus shot", "tetanus booster", "tetanus vaccine", "tetanus toxoid", "td", "dtap", "tetanus prophylaxis", "tetanus update", "update tetanus", "update the tetanus", "tetanus status", "tetanus immunization", "tetanus immunisation", "tetanus vaccination", "tetanus diphtheria pertussis", "tetanus diphtheria and pertussis", "tetanus diphtheria", "tetanus and diphtheria", "boostrix", "adacel", "tdap booster", "tdap vaccine", "tdap shot", "tdap vaccination", "tdap immunization", "tdap immunisation", "td booster", "td vaccine", "td shot", "td vaccination", "td immunization", "td immunisation", "diphtheria toxoid", "diphtheria vaccine", "diphtheria booster", "diphtheria immunization", "diphtheria immunisation", "diphtheria vaccination", "pertussis vaccine", "pertussis booster", "pertussis immunization", "pertussis immunisation", "pertussis vaccination", "whooping cough vaccine", "whooping cough booster", "whooping cough immunization", "whooping cough immunisation", "whooping cough vaccination")
alias("tranexamic_acid", "tranexamic acid", "txa", "t x a", "cyklokapron", "lysteda", "iv txa", "iv tranexamic acid", "txa bolus", "tranexamic acid bolus", "txa push", "tranexamic acid push", "txa drip", "tranexamic acid drip", "txa infusion", "tranexamic acid infusion", "txa gtt", "tranexamic acid gtt", "txa bolus and drip", "tranexamic acid bolus and drip", "txa bolus then drip", "tranexamic acid bolus then drip", "txa bolus and infusion", "tranexamic acid bolus and infusion", "txa bolus then infusion", "tranexamic acid bolus then infusion", "txa load", "tranexamic acid load", "load txa", "load tranexamic acid", "load with txa", "load with tranexamic acid", "txa loading dose", "tranexamic acid loading dose", "loading dose of txa", "loading dose of tranexamic acid", "txa 1 gram", "tranexamic acid 1 gram", "txa 1 g", "tranexamic acid 1 g", "txa 2 grams", "tranexamic acid 2 grams", "txa 2 g", "tranexamic acid 2 g", "a gram of txa", "a gram of tranexamic acid", "gram of txa", "gram of tranexamic acid", "1 gram of txa", "1 gram of tranexamic acid", "one gram of txa", "one gram of tranexamic acid", "2 grams of txa", "2 grams of tranexamic acid", "two grams of txa", "two grams of tranexamic acid", "txa 1 gram over 10 minutes", "tranexamic acid 1 gram over 10 minutes", "txa 1 gram over ten minutes", "tranexamic acid 1 gram over ten minutes", "txa over 10 minutes", "tranexamic acid over 10 minutes", "txa over ten minutes", "tranexamic acid over ten minutes", "txa 1 gram then 1 gram over 8 hours", "tranexamic acid 1 gram then 1 gram over 8 hours", "txa 1 gram then 1 gram over eight hours", "tranexamic acid 1 gram then 1 gram over eight hours", "txa over 8 hours", "tranexamic acid over 8 hours", "txa over eight hours", "tranexamic acid over eight hours", "txa for trauma", "tranexamic acid for trauma", "txa for the trauma", "tranexamic acid for the trauma", "txa for hemorrhage", "tranexamic acid for hemorrhage", "txa for the hemorrhage", "tranexamic acid for the hemorrhage", "txa for bleeding", "tranexamic acid for bleeding", "txa for the bleeding", "tranexamic acid for the bleeding", "txa for the bleed", "tranexamic acid for the bleed", "txa for bleed", "tranexamic acid for bleed", "txa for hemorrhagic shock", "tranexamic acid for hemorrhagic shock", "txa for the hemorrhagic shock", "tranexamic acid for the hemorrhagic shock", "txa for pph", "tranexamic acid for pph", "txa for the pph", "tranexamic acid for the pph", "txa for postpartum hemorrhage", "tranexamic acid for postpartum hemorrhage", "txa for the postpartum hemorrhage", "tranexamic acid for the postpartum hemorrhage", "txa for post partum hemorrhage", "tranexamic acid for post partum hemorrhage", "txa for the post partum hemorrhage", "tranexamic acid for the post partum hemorrhage", "txa for epistaxis", "tranexamic acid for epistaxis", "txa for the epistaxis", "tranexamic acid for the epistaxis", "txa for the nosebleed", "tranexamic acid for the nosebleed", "txa for nosebleed", "tranexamic acid for nosebleed", "txa for hemoptysis", "tranexamic acid for hemoptysis", "txa for the hemoptysis", "tranexamic acid for the hemoptysis", "txa for gi bleed", "tranexamic acid for gi bleed", "txa for the gi bleed", "tranexamic acid for the gi bleed", "txa for hyphema", "tranexamic acid for hyphema", "txa for the hyphema", "tranexamic acid for the hyphema", "txa for angioedema", "tranexamic acid for angioedema", "txa for the angioedema", "tranexamic acid for the angioedema", "txa for hereditary angioedema", "tranexamic acid for hereditary angioedema", "txa for the hereditary angioedema", "tranexamic acid for the hereditary angioedema", "txa for hae", "tranexamic acid for hae", "txa for the hae", "tranexamic acid for the hae", "txa for ace inhibitor angioedema", "tranexamic acid for ace inhibitor angioedema", "txa for the ace inhibitor angioedema", "tranexamic acid for the ace inhibitor angioedema", "txa for acei angioedema", "tranexamic acid for acei angioedema", "txa for the acei angioedema", "tranexamic acid for the acei angioedema", "txa for tbi", "tranexamic acid for tbi", "txa for the tbi", "tranexamic acid for the tbi", "txa for head injury", "tranexamic acid for head injury", "txa for the head injury", "tranexamic acid for the head injury", "txa for the head bleed", "tranexamic acid for the head bleed", "txa for head bleed", "tranexamic acid for head bleed", "txa for sah", "tranexamic acid for sah", "txa for the sah", "tranexamic acid for the sah", "txa for ich", "tranexamic acid for ich", "txa for the ich", "tranexamic acid for the ich", "txa for menorrhagia", "tranexamic acid for menorrhagia", "txa for the menorrhagia", "tranexamic acid for the menorrhagia", "txa for heavy menstrual bleeding", "tranexamic acid for heavy menstrual bleeding", "txa for the heavy menstrual bleeding", "tranexamic acid for the heavy menstrual bleeding", "txa for vaginal bleeding", "tranexamic acid for vaginal bleeding", "txa for the vaginal bleeding", "tranexamic acid for the vaginal bleeding", "txa for hematuria", "tranexamic acid for hematuria", "txa for the hematuria", "tranexamic acid for the hematuria", "txa for dental bleeding", "tranexamic acid for dental bleeding", "txa for the dental bleeding", "tranexamic acid for the dental bleeding", "txa for tooth extraction bleeding", "tranexamic acid for tooth extraction bleeding", "txa for the tooth extraction bleeding", "tranexamic acid for the tooth extraction bleeding", "txa mouthwash", "tranexamic acid mouthwash", "txa rinse", "tranexamic acid rinse", "txa mouth rinse", "tranexamic acid mouth rinse", "topical txa", "topical tranexamic acid", "txa topical", "tranexamic acid topical", "txa soaked gauze", "tranexamic acid soaked gauze", "txa soaked packing", "tranexamic acid soaked packing", "txa pledget", "tranexamic acid pledget", "txa pledgets", "tranexamic acid pledgets", "nebulized txa", "nebulized tranexamic acid", "nebulised txa", "nebulised tranexamic acid", "txa neb", "tranexamic acid neb", "txa nebulizer", "tranexamic acid nebulizer", "txa nebuliser", "tranexamic acid nebuliser", "inhaled txa", "inhaled tranexamic acid", "txa inhaled", "tranexamic acid inhaled", "antifibrinolytic", "an antifibrinolytic", "antifibrinolytics", "anti fibrinolytic", "an anti fibrinolytic", "anti fibrinolytics", "antifibrinolytic therapy", "anti fibrinolytic therapy", "aminocaproic acid", "amicar", "epsilon aminocaproic acid", "eaca")
for p in ["aminocaproic acid", "amicar", "epsilon aminocaproic acid", "eaca"]:
    A["tranexamic_acid"].remove(p); unavailable(p, "Aminocaproic acid is not in the catalog; tranexamic acid is. Not substituted.")

# Stop actions. "stop", "hold", "discontinue", "turn off", "wean off", "shut off" plus the
# drug. The parser keeps "stop" (it is not filler), so "stop the levophed" reaches the
# table as "stop levophed".
# "discontinue", "hold", "turn off", "wean off" and "dc" canonicalise to "stop" in the parser.
STOPWORDS = ["stop"]
STOPS = {"stop_dobutamine": ["dobutamine", "dobuta", "dobutamine drip", "dobutamine infusion"],
         "stop_dopamine": ["dopamine", "dopa", "dopamine drip", "dopamine infusion"],
         "stop_epinephrine": ["epinephrine", "epi", "epinephrine drip", "epi drip", "epinephrine infusion", "epi infusion", "adrenaline"],
         "stop_esmolol": ["esmolol", "brevibloc", "esmolol drip", "esmolol infusion"],
         "stop_labetalol": ["labetalol", "labetalol drip", "labetalol infusion"],
         "stop_nicardipine": ["nicardipine", "cardene", "nicardipine drip", "nicardipine infusion", "cardene drip"],
         "stop_nitroglycerin": ["nitroglycerin", "nitro", "ntg", "nitroglycerin drip", "nitro drip", "ntg drip", "nitroglycerin infusion", "nitro infusion", "nitrates"],
         "stop_nitroprusside": ["nitroprusside", "nipride", "nitroprusside drip", "nipride drip", "nitroprusside infusion"],
         "stop_norepinephrine": ["norepinephrine", "norepi", "levophed", "levo", "noradrenaline", "norepinephrine drip", "norepi drip", "levophed drip", "levo drip", "norepinephrine infusion", "levophed infusion", "pressor", "pressors", "the pressor", "the pressors", "vasopressor", "vasopressors"],
         "stop_phenylephrine": ["phenylephrine", "neo", "neosynephrine", "phenylephrine drip", "neo drip", "phenylephrine infusion", "neo infusion"],
         "stop_vasopressin": ["vasopressin", "vaso", "vasopressin drip", "vaso drip", "vasopressin infusion", "vaso infusion"],
         "stop_ketamine": ["ketamine", "ketamine drip", "ketamine infusion"],
         "stop_propofol": ["propofol", "diprivan", "propofol drip", "propofol infusion", "sedation", "the sedation", "sedation holiday", "sedation vacation"],
         "stop_amiodarone_bolus_infusion": ["amiodarone", "amio", "amiodarone drip", "amio drip", "amiodarone infusion", "amio infusion"],
         "stop_heparin_bolus_drip": ["heparin", "heparin drip", "heparin infusion", "anticoagulation", "the anticoagulation", "the heparin"],
         "stop_procainamide": ["procainamide", "procainamide drip", "procainamide infusion"],
         "stop_octreotide_bolus_infusion": ["octreotide", "sandostatin", "octreotide drip", "octreotide infusion"],
         "stop_na_bicarbonate": ["bicarb", "bicarbonate", "sodium bicarbonate", "sodium bicarb", "bicarb drip", "bicarbonate drip", "bicarb infusion", "bicarbonate infusion"],
         "stop_hypertonic_saline_3": ["hypertonic saline", "hypertonic", "3 percent", "three percent", "3 percent saline", "three percent saline", "hypertonic saline drip", "hypertonic drip", "hypertonic saline infusion", "hypertonic infusion"],
         "stop_insulin": ["insulin", "insulin drip", "insulin infusion", "the insulin"]}
for cid, names in STOPS.items():
    for n in names:
        for s in STOPWORDS: alias(cid, f"{s} {n}", f"{n} off", f"{n} {s}")
for p in ["stop pressor", "stop pressors", "stop the pressor", "stop the pressors", "stop vasopressor", "stop vasopressors", "pressor off", "pressors off",
          "wean off pressor", "wean off pressors", "wean the pressor", "wean the pressors", "wean pressors", "turn off the pressor", "turn off the pressors"]:
    for cid in STOPS:
        if p in A[cid]: A[cid].remove(p)
    ambiguous(p, "stop_norepinephrine", "stop_epinephrine", "stop_vasopressin", "stop_phenylephrine", "stop_dopamine", "stop_dobutamine")
for p in ["stop sedation", "stop the sedation", "hold sedation", "hold the sedation", "sedation holiday", "sedation vacation", "turn off the sedation", "turn off sedation", "wean off sedation", "wean sedation", "wean the sedation", "sedation off", "off sedation"]:
    for cid in STOPS:
        if p in A[cid]: A[cid].remove(p)
    ambiguous(p, "stop_propofol", "stop_ketamine")
for p in ["stop the drip", "stop drip", "stop the infusion", "stop infusion", "stop the drips", "stop drips", "stop everything", "stop all drips", "stop all the drips", "turn off the drip", "turn off the drips", "turn off everything", "hold the drip", "hold the drips", "hold everything", "stop the medication", "stop the medications", "stop the meds", "stop the med", "hold the med", "hold the meds", "hold the medication", "hold the medications", "discontinue the drip", "discontinue the drips", "dc the drip", "dc the drips"]:
    ambiguous(p, *sorted(STOPS))

# Procedures
alias("c_collar", "c collar", "cervical collar", "collar", "hard collar", "aspen collar", "miami j", "miami j collar", "philadelphia collar", "c spine immobilization", "c spine immobilisation", "cervical immobilization", "cervical immobilisation", "spinal immobilization", "spinal immobilisation", "immobilize the c spine", "immobilise the c spine", "c spine precautions", "spinal precautions", "cervical spine precautions", "cervical spine immobilization", "cervical spine immobilisation", "put on a collar", "put a collar on", "collar the patient", "collar them", "collar him", "collar her", "collar on", "in a collar", "keep the collar on", "maintain c spine precautions", "maintain spinal precautions", "maintain cervical spine precautions", "hold c spine", "hold the c spine", "hold cervical spine", "hold the cervical spine", "manual c spine", "manual in line stabilization", "manual inline stabilization", "in line stabilization", "inline stabilization", "milis", "mils", "stabilize the c spine", "stabilise the c spine", "stabilize the neck", "stabilise the neck", "immobilize the neck", "immobilise the neck", "neck immobilization", "neck immobilisation", "neck brace", "cervical brace", "c spine collar", "cervical spine collar")
alias("decontaminate_hazmat_activation", "decontaminate", "decontamination", "decon", "hazmat", "hazmat activation", "activate hazmat", "hazmat decon", "decon the patient", "decontaminate the patient", "strip and decon", "gross decon", "gross decontamination", "wash the patient down", "hose the patient down", "dermal decontamination", "skin decontamination", "external decontamination", "decon shower", "decontamination shower", "decon tent", "decontamination tent", "decon team", "decontamination team", "call hazmat", "call the hazmat team", "hazmat team", "activate the hazmat team", "hazmat protocol", "activate hazmat protocol", "activate the hazmat protocol", "chemical decon", "chemical decontamination", "radiation decon", "radiation decontamination", "biological decon", "biological decontamination", "decontaminate the skin", "decontaminate skin", "wash off the chemical", "wash off the agent", "wash the chemical off", "wash the agent off", "irrigate the skin", "skin irrigation", "copious irrigation of the skin", "remove contaminated clothing", "remove the contaminated clothing", "bag the clothing", "bag the clothes", "bag contaminated clothing", "bag the contaminated clothing")
alias("don_personal_protective_equipment", "ppe", "don ppe", "personal protective equipment", "put on ppe", "gown up", "gown and glove up", "gloves and gown", "protective equipment", "full ppe", "don full ppe", "get in ppe", "ppe up", "protect yourself", "everyone in ppe", "everybody in ppe", "staff in ppe", "team in ppe", "ppe for everyone", "ppe for everybody", "ppe for the staff", "ppe for the team", "ppe on", "ppe first", "ppe before entering", "ppe before entering the room", "don appropriate ppe", "appropriate ppe", "don the appropriate ppe", "level c ppe", "level b ppe", "level a ppe", "level c", "level b", "level a", "hazmat suit", "hazmat suits", "hazmat suit up", "suit up", "gown gloves mask", "gown gloves and mask", "gown gloves mask and eye protection", "gown gloves mask eye protection", "mask gown gloves", "mask gown and gloves", "gloves gown mask", "gloves gown and mask", "eye protection", "face shield", "face shields", "goggles", "n95 and gown", "n95 gown gloves", "n95 gown and gloves", "n95 with gown and gloves", "papr and gown", "papr gown gloves", "papr gown and gloves", "papr with gown and gloves", "double glove", "double gloves", "double gloving", "shoe covers", "boot covers", "bouffant", "hair cover", "hair covers", "cap", "surgical cap", "surgical caps", "bonnet", "bonnets")
for p in ["level c", "level b", "level a", "cap", "goggles", "eye protection", "face shield", "face shields", "bouffant", "bonnet", "bonnets", "hair cover", "hair covers", "shoe covers", "boot covers", "suit up"]:
    if p in A["don_personal_protective_equipment"]: A["don_personal_protective_equipment"].remove(p)
alias("insert_chest_tube", "chest tube", "insert chest tube", "place a chest tube", "put in a chest tube", "tube thoracostomy", "thoracostomy", "thoracostomy tube", "pigtail", "pigtail catheter", "pigtail chest tube", "finger thoracostomy", "chest drain", "intercostal drain", "large bore chest tube", "small bore chest tube", "chest tube on the left", "chest tube on the right", "left chest tube", "right chest tube", "bilateral chest tubes", "chest tubes", "32 french chest tube", "28 french chest tube", "36 french chest tube", "14 french pigtail", "chest tube to suction", "chest tube to water seal", "chest tube to pleurevac", "pleurevac", "atrium", "thoracostomy on the left", "thoracostomy on the right", "left thoracostomy", "right thoracostomy", "bilateral thoracostomies", "bilateral finger thoracostomies", "bilateral finger thoracostomy", "decompress the chest", "decompress the pneumothorax", "decompress the hemothorax", "drain the pneumothorax", "drain the hemothorax", "drain the effusion", "drain the pleural effusion", "drain the chest", "drain the pleural space", "evacuate the pneumothorax", "evacuate the hemothorax", "chest tube for pneumothorax", "chest tube for the pneumothorax", "chest tube for hemothorax", "chest tube for the hemothorax", "chest tube for effusion", "chest tube for the effusion", "chest tube for pleural effusion", "chest tube for the pleural effusion", "chest tube for empyema", "chest tube for the empyema")
for p in ["needle decompression", "needle thoracostomy", "needle the chest", "needle decompress", "needle decompress the chest", "decompress with a needle", "14 gauge to the chest", "14 gauge in the chest", "needle in the second intercostal space", "needle in the fifth intercostal space", "thoracentesis", "tap the chest", "tap the effusion", "pleural tap", "pleurocentesis", "pericardiocentesis", "tap the pericardium", "pericardial tap", "pericardial drain", "pericardial window", "thoracotomy", "ed thoracotomy", "resuscitative thoracotomy", "clamshell", "clamshell thoracotomy", "open the chest", "crack the chest", "reboa"]:
    unavailable(p, "Not in the catalog. The chest procedure available is the chest tube (tube thoracostomy).")
alias("insert_foley_catheter", "foley", "foley catheter", "insert foley", "place a foley", "put in a foley", "urinary catheter", "bladder catheter", "urethral catheter", "indwelling catheter", "indwelling urinary catheter", "idc", "cath the bladder", "catheterize the bladder", "catheterise the bladder", "catheterize", "catheterise", "foley for urine output", "foley for strict i and o", "foley for strict ins and outs", "foley for strict io", "foley to gravity", "foley to drainage", "foley to bag", "foley for retention", "foley for the retention", "foley for urinary retention", "foley for the urinary retention", "decompress the bladder", "drain the bladder", "empty the bladder", "relieve the retention", "relieve the obstruction", "relieve the urinary retention", "relieve the urinary obstruction", "coude", "coude catheter", "coude foley", "16 french foley", "14 french foley", "18 french foley", "three way foley", "3 way foley", "three way catheter", "3 way catheter", "cbi", "continuous bladder irrigation", "bladder irrigation", "irrigate the bladder", "foley with temperature probe", "temperature sensing foley", "temp sensing foley", "foley with a temperature probe", "foley temp probe", "urine output", "strict urine output", "monitor urine output", "measure urine output", "strict ins and outs", "strict i and o", "strict io", "strict i o", "ins and outs", "i and o", "io monitoring", "i and o monitoring", "urine output monitoring", "hourly urine output", "hourly urine outputs", "hourly uop", "uop", "strict uop", "monitor uop", "measure uop", "follow urine output", "follow uop", "follow the urine output", "follow the uop", "trend urine output", "trend uop", "trend the urine output", "trend the uop", "watch urine output", "watch uop", "watch the urine output", "watch the uop", "check urine output", "check uop", "check the urine output", "check the uop", "urine output goal", "uop goal", "goal urine output", "goal uop", "urine output of 0 5 per kilo per hour", "uop of 0 5 per kilo per hour", "urine output 0 5 per kilo per hour", "uop 0 5 per kilo per hour", "0 5 per kilo per hour urine output", "0 5 per kilo per hour uop", "urine output of 30 an hour", "uop of 30 an hour", "urine output 30 an hour", "uop 30 an hour", "30 an hour urine output", "30 an hour uop", "urine output greater than 30", "uop greater than 30", "urine output over 30", "uop over 30", "urine output above 30", "uop above 30", "urine output of at least 30", "uop of at least 30")
for p in ["straight cath", "in and out cath", "in and out catheter", "straight catheter", "straight catheterization", "straight catheterisation", "suprapubic catheter", "suprapubic", "suprapubic tap", "suprapubic aspiration", "bladder tap", "sp catheter", "sp tube", "suprapubic tube", "cystostomy", "suprapubic cystostomy", "condom catheter", "texas catheter", "purewick", "external catheter", "external urinary catheter"]:
    unavailable(p, "Not in the catalog. The urinary catheter available is the indwelling Foley.")
alias("lower_head_of_bed", "lower head of bed", "lower the head of the bed", "head of bed down", "lay flat", "lay the patient flat", "lie flat", "lie the patient flat", "supine", "supine position", "put the patient flat", "bed flat", "flatten the bed", "head of the bed flat", "hob flat", "hob down", "lower hob", "lower the hob", "lay them flat", "lay him flat", "lay her flat", "lie them flat", "lie him flat", "lie her flat", "lay the patient down", "lay them down", "lay him down", "lay her down", "lie the patient down", "lie them down", "lie him down", "lie her down", "lay down", "lie down", "lay back", "lie back", "lay the patient back", "lay them back", "lay him back", "lay her back", "recline", "recline the patient", "recline them", "recline him", "recline her", "recline the bed", "flat on the back", "flat on their back", "flat on his back", "flat on her back", "on their back", "on his back", "on her back", "put them on their back", "put him on his back", "put her on her back", "put the patient on their back", "head down", "head of bed flat", "head of bed to zero", "head of bed at zero", "head of bed zero", "hob zero", "hob to zero", "hob at zero", "hob 0", "hob to 0", "hob at 0", "head of bed 0", "head of bed to 0", "head of bed at 0", "zero degrees", "0 degrees", "bed to zero", "bed to 0", "bed at zero", "bed at 0", "bed zero", "bed 0", "flat bed", "make the bed flat", "make the patient flat", "get the patient flat", "get them flat", "get him flat", "get her flat", "put them flat", "put him flat", "put her flat", "position flat", "position supine", "position the patient supine", "position them supine", "position him supine", "position her supine", "supine positioning", "flat positioning", "lower the bed", "lower the head", "drop the head of the bed", "drop the head", "drop the hob", "drop the bed", "take the head of the bed down", "take the head down", "take the hob down", "take the bed down", "bring the head of the bed down", "bring the head down", "bring the hob down", "bring the bed down", "put the head of the bed down", "put the head down", "put the hob down", "put the bed down", "head of the bed down", "head of bed all the way down", "head of the bed all the way down", "hob all the way down", "bed all the way down", "all the way down", "all the way flat", "completely flat", "totally flat", "fully flat", "fully supine", "completely supine", "totally supine")
for p in ["trendelenburg", "trendelenberg", "t burg", "tburg", "head down tilt", "head down position", "legs up", "raise the legs", "elevate the legs", "passive leg raise", "leg raise", "plr", "reverse trendelenburg", "reverse trendelenberg", "reverse t burg", "head of bed up", "head of bed 30", "head of bed at 30", "head of bed to 30", "hob 30", "hob at 30", "hob to 30", "hob up", "raise the head of the bed", "raise the head of bed", "elevate the head of the bed", "elevate the head of bed", "sit the patient up", "sit them up", "sit him up", "sit her up", "sit up", "upright", "sit upright", "sitting up", "sitting upright", "high fowlers", "fowlers", "semi fowlers", "semi recumbent", "left lateral decubitus", "right lateral decubitus", "lateral decubitus", "left lateral", "right lateral", "recovery position", "on the left side", "on the right side", "on their side", "on his side", "on her side", "roll the patient", "roll them", "roll him", "roll her", "log roll", "logroll", "prone", "prone the patient", "prone them", "prone him", "prone her", "prone position", "prone positioning", "proning", "awake proning", "self proning", "tripod", "tripod position", "tripoding", "knee chest", "knee chest position", "knees to chest", "left uterine displacement", "lud", "tilt the patient", "tilt them", "tilt him", "tilt her", "tilt to the left", "left tilt", "wedge", "wedge under the hip", "wedge under the right hip", "hip wedge", "displace the uterus", "manually displace the uterus"]:
    unavailable(p, "Not in the catalog. The positioning acts available are lowering the head of the bed and positioning for intubation.")
alias("lumbar_puncture", "lp", "lumbar puncture", "spinal tap", "do an lp", "perform an lp", "perform a lumbar puncture", "do a lumbar puncture", "get csf", "obtain csf", "csf sample", "sample the csf", "lp for csf", "lumbar puncture for csf", "opening pressure", "lp with opening pressure", "lumbar puncture with opening pressure", "lp with an opening pressure", "lumbar puncture with an opening pressure", "measure the opening pressure", "check the opening pressure", "get an opening pressure", "lp the patient", "lp them", "lp him", "lp her", "tap the patient", "tap them", "tap him", "tap her", "spinal", "the tap", "a tap", "an lp", "the lp", "a lumbar puncture", "the lumbar puncture", "a spinal tap", "the spinal tap", "lp now", "lp stat", "stat lp", "lp before antibiotics", "lp after antibiotics", "lp after the ct", "lp after ct", "lp after the head ct", "lp after head ct", "lp after imaging", "lp after the imaging", "lp for meningitis", "lp for the meningitis", "lp to rule out meningitis", "lumbar puncture to rule out meningitis", "lp for sah", "lp for the sah", "lp to rule out sah", "lumbar puncture to rule out sah", "lp for subarachnoid", "lp for the subarachnoid", "lp to rule out subarachnoid", "lumbar puncture to rule out subarachnoid", "lp for xanthochromia", "lp for the xanthochromia", "lp for idiopathic intracranial hypertension", "lp for iih", "lp for the iih", "lp for pseudotumor", "lp for the pseudotumor", "lp for pseudotumor cerebri", "lp for the pseudotumor cerebri", "therapeutic lp", "therapeutic lumbar puncture", "diagnostic lp", "diagnostic lumbar puncture", "large volume lp", "large volume lumbar puncture", "high volume lp", "high volume lumbar puncture", "lp with fluoro", "lp under fluoro", "lp with fluoroscopy", "lp under fluoroscopy", "fluoro guided lp", "fluoroscopy guided lp", "ir lp", "ir guided lp", "lp by ir", "lp with ir", "lp under ultrasound", "lp with ultrasound", "ultrasound guided lp", "ultrasound assisted lp", "lp in the lateral decubitus", "lp sitting up", "lp sitting", "lp lateral", "lp lateral decubitus", "lp in the sitting position", "lp in the lateral position", "lp in the lateral decubitus position", "lp in lateral decubitus", "lp in lateral decubitus position", "lp in sitting position", "lp in the sitting", "lp sitting position")
for p in ["tap the patient", "tap them", "tap him", "tap her", "spinal", "the tap", "a tap"]:
    if p in A["lumbar_puncture"]: A["lumbar_puncture"].remove(p)
alias("place_nasogastric_tube", "ng tube", "ngt", "nasogastric tube", "nasogastric", "ng", "place an ng", "place an ng tube", "put in an ng", "put in an ng tube", "drop an ng", "drop an ng tube", "insert an ng", "insert an ng tube", "ng to suction", "ng tube to suction", "ng to low intermittent suction", "ng tube to low intermittent suction", "ngt to suction", "ngt to lis", "ng to lis", "ng decompression", "gastric decompression", "decompress the stomach", "salem sump", "sump", "nasogastric decompression", "ng to low wall suction", "ng tube to low wall suction", "ngt to low wall suction", "ng to lws", "ng tube to lws", "ngt to lws", "ng to continuous suction", "ng tube to continuous suction", "ngt to continuous suction", "ng to intermittent suction", "ng tube to intermittent suction", "ngt to intermittent suction", "ng to gravity", "ng tube to gravity", "ngt to gravity", "ng tube placement", "ngt placement", "nasogastric tube placement", "ng placement", "nasogastric placement", "nasogastric tube insertion", "ng tube insertion", "ngt insertion", "ng insertion", "nasogastric insertion", "ng tube for decompression", "ngt for decompression", "nasogastric tube for decompression", "ng for decompression", "nasogastric for decompression", "ng tube for lavage", "ngt for lavage", "nasogastric tube for lavage", "ng for lavage", "nasogastric for lavage", "ng tube for charcoal", "ngt for charcoal", "nasogastric tube for charcoal", "ng for charcoal", "nasogastric for charcoal", "ng tube for wbi", "ngt for wbi", "nasogastric tube for wbi", "ng for wbi", "nasogastric for wbi", "ng tube for whole bowel irrigation", "ngt for whole bowel irrigation", "nasogastric tube for whole bowel irrigation", "ng for whole bowel irrigation", "nasogastric for whole bowel irrigation", "ng tube for feeding", "ngt for feeding", "nasogastric tube for feeding", "ng for feeding", "nasogastric for feeding", "ng tube for feeds", "ngt for feeds", "nasogastric tube for feeds", "ng for feeds", "nasogastric for feeds", "ng tube for meds", "ngt for meds", "nasogastric tube for meds", "ng for meds", "nasogastric for meds", "ng tube for medications", "ngt for medications", "nasogastric tube for medications", "ng for medications", "nasogastric for medications", "ng tube for the sbo", "ngt for the sbo", "nasogastric tube for the sbo", "ng for the sbo", "nasogastric for the sbo", "ng tube for sbo", "ngt for sbo", "nasogastric tube for sbo", "ng for sbo", "nasogastric for sbo", "ng tube for the obstruction", "ngt for the obstruction", "nasogastric tube for the obstruction", "ng for the obstruction", "nasogastric for the obstruction", "ng tube for obstruction", "ngt for obstruction", "nasogastric tube for obstruction", "ng for obstruction", "nasogastric for obstruction", "ng tube for the ileus", "ngt for the ileus", "nasogastric tube for the ileus", "ng for the ileus", "nasogastric for the ileus", "ng tube for ileus", "ngt for ileus", "nasogastric tube for ileus", "ng for ileus", "nasogastric for ileus", "ng tube for vomiting", "ngt for vomiting", "nasogastric tube for vomiting", "ng for vomiting", "nasogastric for vomiting", "ng tube for the vomiting", "ngt for the vomiting", "nasogastric tube for the vomiting", "ng for the vomiting", "nasogastric for the vomiting", "ng tube for the gi bleed", "ngt for the gi bleed", "nasogastric tube for the gi bleed", "ng for the gi bleed", "nasogastric for the gi bleed", "ng tube for gi bleed", "ngt for gi bleed", "nasogastric tube for gi bleed", "ng for gi bleed", "nasogastric for gi bleed", "ng aspirate", "ng aspiration", "nasogastric aspirate", "nasogastric aspiration", "ng lavage", "nasogastric lavage", "gastric lavage", "lavage", "stomach pump", "pump the stomach", "pump their stomach", "pump his stomach", "pump her stomach", "pump the patients stomach")
for p in ["ng lavage", "nasogastric lavage", "gastric lavage", "lavage", "stomach pump", "pump the stomach", "pump their stomach", "pump his stomach", "pump her stomach", "pump the patients stomach", "ng aspirate", "ng aspiration", "nasogastric aspirate", "nasogastric aspiration"]:
    A["place_nasogastric_tube"].remove(p); unavailable(p, "Gastric lavage is not in the catalog. The NG tube is, and whole bowel irrigation by NG tube is.")
alias("place_orogastric_tube", "og tube", "ogt", "orogastric tube", "orogastric", "og", "place an og", "place an og tube", "put in an og", "put in an og tube", "drop an og", "drop an og tube", "insert an og", "insert an og tube", "og to suction", "og tube to suction", "ogt to suction", "ogt to lis", "og to lis", "orogastric decompression", "og to low intermittent suction", "og tube to low intermittent suction", "og to low wall suction", "og tube to low wall suction", "ogt to low wall suction", "og to lws", "og tube to lws", "ogt to lws", "og to gravity", "og tube to gravity", "ogt to gravity", "og tube placement", "ogt placement", "orogastric tube placement", "og placement", "orogastric placement", "orogastric tube insertion", "og tube insertion", "ogt insertion", "og insertion", "orogastric insertion", "og tube after intubation", "ogt after intubation", "orogastric tube after intubation", "og after intubation", "orogastric after intubation", "og tube post intubation", "ogt post intubation", "orogastric tube post intubation", "og post intubation", "orogastric post intubation", "og tube once intubated", "ogt once intubated", "orogastric tube once intubated", "og once intubated", "orogastric once intubated", "og tube for decompression", "ogt for decompression", "orogastric tube for decompression", "og for decompression", "orogastric for decompression", "og tube for charcoal", "ogt for charcoal", "orogastric tube for charcoal", "og for charcoal", "orogastric for charcoal", "og tube for the intubated patient", "ogt for the intubated patient", "orogastric tube for the intubated patient", "og for the intubated patient", "orogastric for the intubated patient", "og tube since intubated", "ogt since intubated", "orogastric tube since intubated", "og since intubated", "orogastric since intubated", "og tube because intubated", "ogt because intubated", "orogastric tube because intubated", "og because intubated", "orogastric because intubated", "og tube in the intubated patient", "ogt in the intubated patient", "orogastric tube in the intubated patient", "og in the intubated patient", "orogastric in the intubated patient", "og tube now that they are intubated", "ogt now that they are intubated", "orogastric tube now that they are intubated", "og now that they are intubated", "orogastric now that they are intubated", "og tube now that the patient is intubated", "ogt now that the patient is intubated", "orogastric tube now that the patient is intubated", "og now that the patient is intubated", "orogastric now that the patient is intubated", "og tube now that he is intubated", "ogt now that he is intubated", "orogastric tube now that he is intubated", "og now that he is intubated", "orogastric now that he is intubated", "og tube now that she is intubated", "ogt now that she is intubated", "orogastric tube now that she is intubated", "og now that she is intubated", "orogastric now that she is intubated")
ambiguous("gastric tube", "place_nasogastric_tube", "place_orogastric_tube")
ambiguous("stomach tube", "place_nasogastric_tube", "place_orogastric_tube")
ambiguous("tube to suction", "place_nasogastric_tube", "place_orogastric_tube")
ambiguous("tube for decompression", "place_nasogastric_tube", "place_orogastric_tube")
alias("place_patient_on_isolation_precautions", "isolation", "isolate the patient", "isolate them", "isolate him", "isolate her", "isolation precautions", "isolation room", "put the patient in isolation", "put them in isolation", "put him in isolation", "put her in isolation", "private room", "single room", "move to a private room", "move to a single room", "isolate", "isolation precaution", "on isolation", "in isolation", "isolated", "isolation for the patient", "isolation for them", "isolation for him", "isolation for her", "put on isolation", "put the patient on isolation", "put them on isolation", "put him on isolation", "put her on isolation", "place on isolation", "place the patient on isolation", "place them on isolation", "place him on isolation", "place her on isolation", "place in isolation", "place the patient in isolation", "place them in isolation", "place him in isolation", "place her in isolation", "move to isolation", "move the patient to isolation", "move them to isolation", "move him to isolation", "move her to isolation", "move to an isolation room", "move the patient to an isolation room", "move them to an isolation room", "move him to an isolation room", "move her to an isolation room", "isolation room please", "isolation room stat", "isolation room now", "get an isolation room", "get the isolation room", "find an isolation room", "find the isolation room", "need an isolation room", "need the isolation room", "we need an isolation room", "we need the isolation room", "isolation please", "isolation stat", "isolation now", "standard precautions", "universal precautions", "standard precaution", "universal precaution", "infection control", "infection control precautions", "infection prevention", "infection prevention precautions", "call infection control", "notify infection control", "page infection control", "infection control to bedside", "infection control at bedside", "infection control consult", "consult infection control", "infection control consultation", "infection prevention consult", "consult infection prevention", "infection prevention consultation", "call infection prevention", "notify infection prevention", "page infection prevention", "infection prevention to bedside", "infection prevention at bedside", "epidemiology", "hospital epidemiology", "call epidemiology", "notify epidemiology", "page epidemiology", "call hospital epidemiology", "notify hospital epidemiology", "page hospital epidemiology", "public health", "call public health", "notify public health", "page public health", "department of health", "call the department of health", "notify the department of health", "page the department of health", "health department", "call the health department", "notify the health department", "page the health department", "cdc", "call the cdc", "notify the cdc", "page the cdc", "reportable", "reportable disease", "reportable condition", "report to public health", "report to the health department", "report to the department of health", "report to the cdc", "report to epidemiology", "report to infection control", "report to infection prevention")
for p in ["standard precautions", "universal precautions", "standard precaution", "universal precaution", "infection control", "infection control precautions", "infection prevention", "infection prevention precautions", "call infection control", "notify infection control", "page infection control", "infection control to bedside", "infection control at bedside", "infection control consult", "consult infection control", "infection control consultation", "infection prevention consult", "consult infection prevention", "infection prevention consultation", "call infection prevention", "notify infection prevention", "page infection prevention", "infection prevention to bedside", "infection prevention at bedside", "epidemiology", "hospital epidemiology", "call epidemiology", "notify epidemiology", "page epidemiology", "call hospital epidemiology", "notify hospital epidemiology", "page hospital epidemiology", "public health", "call public health", "notify public health", "page public health", "department of health", "call the department of health", "notify the department of health", "page the department of health", "health department", "call the health department", "notify the health department", "page the health department", "cdc", "call the cdc", "notify the cdc", "page the cdc", "reportable", "reportable disease", "reportable condition", "report to public health", "report to the health department", "report to the department of health", "report to the cdc", "report to epidemiology", "report to infection control", "report to infection prevention"]:
    A["place_patient_on_isolation_precautions"].remove(p); unavailable(p, "Notifying infection control or public health is a consult, and consults are not voice orders here.")
for p in ["droplet and contact precautions", "contact and droplet precautions", "droplet and contact", "contact and droplet", "droplet contact precautions", "contact droplet precautions", "droplet plus contact", "contact plus droplet", "droplet plus contact precautions", "contact plus droplet precautions"]:
    expand(p, "droplet_precautions", "contact_precautions")
for p in ["airborne and contact precautions", "contact and airborne precautions", "airborne and contact", "contact and airborne", "airborne contact precautions", "contact airborne precautions", "airborne plus contact", "contact plus airborne", "airborne plus contact precautions", "contact plus airborne precautions"]:
    expand(p, "airborne_precautions", "contact_precautions")
for p in ["airborne and droplet precautions", "droplet and airborne precautions", "airborne and droplet", "droplet and airborne", "airborne droplet precautions", "droplet airborne precautions", "airborne plus droplet", "droplet plus airborne", "airborne plus droplet precautions", "droplet plus airborne precautions"]:
    expand(p, "airborne_precautions", "droplet_precautions")
for p in ["full isolation", "full precautions", "all precautions", "every precaution", "airborne contact and droplet", "airborne droplet and contact", "contact airborne and droplet", "contact droplet and airborne", "droplet airborne and contact", "droplet contact and airborne", "airborne contact droplet", "airborne droplet contact", "contact airborne droplet", "contact droplet airborne", "droplet airborne contact", "droplet contact airborne", "airborne contact and droplet precautions", "airborne droplet and contact precautions", "contact airborne and droplet precautions", "contact droplet and airborne precautions", "droplet airborne and contact precautions", "droplet contact and airborne precautions", "airborne contact droplet precautions", "airborne droplet contact precautions", "contact airborne droplet precautions", "contact droplet airborne precautions", "droplet airborne contact precautions", "droplet contact airborne precautions"]:
    expand(p, "airborne_precautions", "droplet_precautions", "contact_precautions")
for p in ["precautions", "precaution", "isolation type", "what precautions", "which precautions", "transmission based precautions", "transmission precautions", "special precautions", "extra precautions", "additional precautions", "enhanced precautions", "appropriate precautions", "the appropriate precautions", "appropriate isolation", "the appropriate isolation", "proper precautions", "the proper precautions", "proper isolation", "the proper isolation", "correct precautions", "the correct precautions", "correct isolation", "the correct isolation", "right precautions", "the right precautions", "right isolation", "the right isolation", "necessary precautions", "the necessary precautions", "necessary isolation", "the necessary isolation", "required precautions", "the required precautions", "required isolation", "the required isolation", "indicated precautions", "the indicated precautions", "indicated isolation", "the indicated isolation", "recommended precautions", "the recommended precautions", "recommended isolation", "the recommended isolation", "usual precautions", "the usual precautions", "usual isolation", "the usual isolation", "routine precautions", "the routine precautions", "routine isolation", "the routine isolation", "standard isolation", "the standard isolation", "normal precautions", "the normal precautions", "normal isolation", "the normal isolation", "regular precautions", "the regular precautions", "regular isolation", "the regular isolation", "typical precautions", "the typical precautions", "typical isolation", "the typical isolation", "isolation precautions as appropriate", "precautions as appropriate", "isolation as appropriate", "isolation precautions as indicated", "precautions as indicated", "isolation as indicated", "isolation precautions as needed", "precautions as needed", "isolation as needed", "isolation precautions per protocol", "precautions per protocol", "isolation per protocol", "isolation precautions per policy", "precautions per policy", "isolation per policy"]:
    ambiguous(p, "droplet_precautions", "contact_precautions", "airborne_precautions", "place_patient_on_isolation_precautions")
alias("whole_bowel_irrigation_by_ng_tube", "whole bowel irrigation", "wbi", "bowel irrigation", "golytely", "go lytely", "polyethylene glycol", "peg solution", "peg 3350", "whole bowel irrigation by ng", "whole bowel irrigation by ng tube", "whole bowel irrigation via ng", "whole bowel irrigation via ng tube", "golytely by ng", "golytely via ng", "golytely by ng tube", "golytely via ng tube", "golytely through the ng", "peg through the ng", "polyethylene glycol through the ng", "irrigate the bowel", "irrigate the gut", "flush the gut", "flush the bowel", "flush the gi tract", "irrigate the gi tract", "wbi by ng", "wbi via ng", "wbi by ng tube", "wbi via ng tube", "wbi through the ng", "wbi through the ng tube", "bowel irrigation by ng", "bowel irrigation via ng", "bowel irrigation by ng tube", "bowel irrigation via ng tube", "bowel irrigation through the ng", "bowel irrigation through the ng tube", "golytely at 2 liters an hour", "golytely at two liters an hour", "golytely 2 liters an hour", "golytely two liters an hour", "golytely at 1 liter an hour", "golytely at one liter an hour", "golytely 1 liter an hour", "golytely one liter an hour", "golytely at 500 an hour", "golytely at five hundred an hour", "golytely 500 an hour", "golytely five hundred an hour", "golytely until clear", "golytely until the effluent is clear", "golytely until effluent is clear", "golytely until rectal effluent is clear", "golytely until the rectal effluent is clear", "wbi until clear", "wbi until the effluent is clear", "wbi until effluent is clear", "wbi until rectal effluent is clear", "wbi until the rectal effluent is clear", "whole bowel irrigation until clear", "whole bowel irrigation until the effluent is clear", "whole bowel irrigation until effluent is clear", "whole bowel irrigation until rectal effluent is clear", "whole bowel irrigation until the rectal effluent is clear", "bowel irrigation until clear", "bowel irrigation until the effluent is clear", "bowel irrigation until effluent is clear", "bowel irrigation until rectal effluent is clear", "bowel irrigation until the rectal effluent is clear", "peg until clear", "peg until the effluent is clear", "peg until effluent is clear", "peg until rectal effluent is clear", "peg until the rectal effluent is clear", "polyethylene glycol until clear", "polyethylene glycol until the effluent is clear", "polyethylene glycol until effluent is clear", "polyethylene glycol until rectal effluent is clear", "polyethylene glycol until the rectal effluent is clear", "wbi for the packer", "wbi for the body packer", "wbi for body packing", "wbi for the body packing", "wbi for the stuffer", "wbi for the body stuffer", "wbi for body stuffing", "wbi for the body stuffing", "wbi for the iron", "wbi for iron", "wbi for the iron overdose", "wbi for iron overdose", "wbi for the lithium", "wbi for lithium", "wbi for the lithium overdose", "wbi for lithium overdose", "wbi for the sustained release", "wbi for sustained release", "wbi for the extended release", "wbi for extended release", "wbi for the enteric coated", "wbi for enteric coated", "wbi for the sr", "wbi for sr", "wbi for the xr", "wbi for xr", "wbi for the er", "wbi for er", "wbi for the potassium", "wbi for potassium", "wbi for the potassium overdose", "wbi for potassium overdose", "wbi for the kcl", "wbi for kcl", "wbi for the kcl overdose", "wbi for kcl overdose", "wbi for the metals", "wbi for metals", "wbi for the heavy metals", "wbi for heavy metals", "wbi for the lead", "wbi for lead", "wbi for the lead overdose", "wbi for lead overdose", "wbi for the arsenic", "wbi for arsenic", "wbi for the arsenic overdose", "wbi for arsenic overdose", "wbi for the mercury", "wbi for mercury", "wbi for the mercury overdose", "wbi for mercury overdose", "wbi for the button battery", "wbi for button battery", "wbi for the batteries", "wbi for batteries", "wbi for the magnets", "wbi for magnets", "wbi for the foreign body", "wbi for foreign body", "wbi for the foreign bodies", "wbi for foreign bodies", "wbi for the patch", "wbi for patch", "wbi for the patches", "wbi for patches", "wbi for the fentanyl patch", "wbi for fentanyl patch", "wbi for the fentanyl patches", "wbi for fentanyl patches", "wbi for the drug packets", "wbi for drug packets", "wbi for the packets", "wbi for packets", "wbi for the baggies", "wbi for baggies", "wbi for the balloons", "wbi for balloons", "wbi for the condoms", "wbi for condoms", "wbi for the pellets", "wbi for pellets")
for p in ["peg", "peg solution", "peg 3350", "polyethylene glycol", "miralax", "bowel prep", "bowel regimen", "laxative", "laxatives", "enema", "enemas", "fleet enema", "fleets", "soap suds enema", "tap water enema", "mineral oil enema", "lactulose enema", "kayexalate enema", "kayexalate", "sodium polystyrene sulfonate", "sps", "lokelma", "sodium zirconium cyclosilicate", "patiromer", "veltassa", "potassium binder", "potassium binders", "k binder", "k binders", "cation exchange resin", "resin", "senna", "senokot", "docusate", "colace", "bisacodyl", "dulcolax", "magnesium citrate", "mag citrate", "milk of magnesia", "mom", "sorbitol", "cathartic", "cathartics", "disimpaction", "manual disimpaction", "disimpact", "rectal tube", "flexiseal", "flexi seal", "rectal trumpet", "nasal trumpet", "nasopharyngeal airway", "npa", "oral airway", "oropharyngeal airway", "opa"]:
    if p in A["whole_bowel_irrigation_by_ng_tube"]: A["whole_bowel_irrigation_by_ng_tube"].remove(p)
    unavailable(p, "Not in the catalog.")

# Blood bank
alias("transfuse_prbc", "prbc", "prbcs", "packed red blood cells", "packed red cells", "packed cells", "red cells", "red blood cells", "rbc", "rbcs", "transfuse", "transfuse blood", "transfuse prbc", "transfuse prbcs", "transfuse packed red blood cells", "transfuse packed cells", "transfuse red cells", "transfuse red blood cells", "give blood", "blood transfusion", "unit of blood", "units of blood", "unit of prbc", "units of prbc", "unit of prbcs", "units of prbcs", "unit of packed cells", "units of packed cells", "unit of packed red blood cells", "units of packed red blood cells", "unit of red cells", "units of red cells", "1 unit of blood", "one unit of blood", "2 units of blood", "two units of blood", "1 unit of prbc", "one unit of prbc", "2 units of prbc", "two units of prbc", "1 unit of prbcs", "2 units of prbcs", "two units of prbcs", "1 unit of packed cells", "2 units of packed cells", "two units of packed cells", "o neg", "o negative", "o neg blood", "o negative blood", "o positive", "o pos", "o pos blood", "o positive blood", "uncrossmatched blood", "uncrossmatched", "uncrossed blood", "emergency release blood", "emergency release", "emergency blood", "universal donor blood", "type specific blood", "crossmatched blood", "cross matched blood", "hang blood", "hang a unit", "hang 2 units", "hang two units", "hang prbc", "hang prbcs", "hang packed cells", "hang red cells", "start blood", "start a unit", "start 2 units", "start two units", "start prbc", "start prbcs", "warm blood", "warmed blood", "blood through the rapid infuser", "blood through the level one", "blood through the belmont", "pressure bag blood", "blood under pressure", "push blood", "push a unit", "push 2 units", "push two units", "bolus blood", "blood wide open", "unit wide open", "2 units wide open", "prbc wide open", "prbcs wide open", "blood stat", "prbc stat", "prbcs stat", "blood now", "unit of o neg", "units of o neg", "unit of o negative", "units of o negative", "2 units of o neg", "two units of o neg", "2 units of o negative", "two units of o negative", "1 unit of o neg", "one unit of o neg", "4 units of blood", "four units of blood", "4 units of prbc", "four units of prbc", "4 units of prbcs", "four units of prbcs", "3 units of blood", "three units of blood", "3 units of prbc", "three units of prbc", "6 units of blood", "six units of blood", "6 units of prbc", "six units of prbc", "the blood", "blood products")
for p in ["the blood", "blood products", "transfuse"]:
    A["transfuse_prbc"].remove(p)
ambiguous("blood", "transfuse_prbc", "blood_type_and_screen")
ambiguous("blood products", "transfuse_prbc", "transfuse_ffp", "transfuse_platelets")
ambiguous("transfuse", "transfuse_prbc", "transfuse_ffp", "transfuse_platelets")
ambiguous("transfusion", "transfuse_prbc", "transfuse_ffp", "transfuse_platelets")
for p in ["whole blood", "low titer o whole blood", "ltowb", "low titer whole blood", "fresh whole blood", "cell saver", "autotransfusion", "auto transfusion", "rapid infuser", "level one", "level 1", "belmont", "rapid transfuser", "blood warmer"]:
    unavailable(p, "Not in the catalog. Blood products available: pRBC, FFP, platelets, PCC, factor VIII, factor IX, IVIG.")
alias("transfuse_ffp", "ffp", "fresh frozen plasma", "plasma", "transfuse ffp", "transfuse plasma", "transfuse fresh frozen plasma", "give ffp", "give plasma", "unit of ffp", "units of ffp", "unit of plasma", "units of plasma", "unit of fresh frozen plasma", "units of fresh frozen plasma", "2 units of ffp", "two units of ffp", "4 units of ffp", "four units of ffp", "2 units of plasma", "two units of plasma", "4 units of plasma", "four units of plasma", "2 ffp", "two ffp", "4 ffp", "four ffp", "2 units ffp", "two units ffp", "4 units ffp", "four units ffp", "hang ffp", "hang plasma", "start ffp", "start plasma", "thawed plasma", "liquid plasma", "ab plasma", "octaplas", "solvent detergent plasma", "15 per kilo ffp", "15 per kilo plasma", "15 cc per kilo ffp", "15 ml per kilo ffp", "10 per kilo ffp", "10 cc per kilo ffp", "10 ml per kilo ffp", "ffp 15 per kilo", "plasma 15 per kilo", "ffp 10 per kilo", "plasma 10 per kilo")
alias("transfuse_platelets", "platelets", "transfuse platelets", "give platelets", "platelet transfusion", "unit of platelets", "units of platelets", "pack of platelets", "packs of platelets", "bag of platelets", "bags of platelets", "pool of platelets", "pooled platelets", "apheresis platelets", "single donor platelets", "random donor platelets", "6 pack of platelets", "six pack of platelets", "1 unit of platelets", "one unit of platelets", "2 units of platelets", "two units of platelets", "hang platelets", "start platelets", "plt", "plts", "transfuse plt", "transfuse plts", "give plt", "give plts", "hang plt", "hang plts", "unit of plt", "units of plt", "unit of plts", "units of plts", "platelets stat", "platelets now", "platelet", "a platelet transfusion", "a unit of platelets", "a pack of platelets", "a bag of platelets", "a pool of platelets", "a six pack of platelets", "a 6 pack of platelets")
alias("prothrombin_complex_concentrate", "pcc", "kcentra", "prothrombin complex concentrate", "prothrombin complex", "4 factor pcc", "four factor pcc", "4 factor", "four factor", "4 f pcc", "four f pcc", "4fpcc", "beriplex", "octaplex", "kcentra 25 per kilo", "pcc 25 per kilo", "kcentra 50 per kilo", "pcc 50 per kilo", "kcentra 2000", "pcc 2000", "kcentra 2000 units", "pcc 2000 units", "kcentra 1500", "pcc 1500", "kcentra 1500 units", "pcc 1500 units", "kcentra 3000", "pcc 3000", "kcentra 3000 units", "pcc 3000 units", "fixed dose kcentra", "fixed dose pcc", "weight based kcentra", "weight based pcc", "give kcentra", "give pcc", "kcentra stat", "pcc stat", "kcentra now", "pcc now", "warfarin reversal", "coumadin reversal", "reverse the warfarin", "reverse the coumadin", "reverse warfarin", "reverse coumadin")
for p in ["warfarin reversal", "coumadin reversal", "reverse the warfarin", "reverse the coumadin", "reverse warfarin", "reverse coumadin"]:
    A["prothrombin_complex_concentrate"].remove(p); ambiguous(p, "prothrombin_complex_concentrate", "transfuse_ffp")
for p in ["reverse the inr", "reverse inr", "reverse anticoagulation", "reverse the anticoagulation", "reversal", "reversal agent", "anticoagulation reversal", "correct the inr", "correct the coagulopathy", "reverse the coagulopathy", "fix the inr", "fix the coagulopathy", "reverse the blood thinner", "reverse the blood thinners", "reverse blood thinners"]:
    ambiguous(p, "prothrombin_complex_concentrate", "transfuse_ffp", "transfuse_platelets")
for p in ["reverse the doac", "reverse doac", "doac reversal", "reverse the xarelto", "reverse xarelto", "reverse the eliquis", "reverse eliquis", "reverse the apixaban", "reverse apixaban", "reverse the rivaroxaban", "reverse rivaroxaban", "reverse the factor xa inhibitor", "reverse factor xa inhibitor", "factor xa reversal", "andexxa", "andexanet", "andexanet alfa", "reverse the pradaxa", "reverse pradaxa", "reverse the dabigatran", "reverse dabigatran", "idarucizumab", "praxbind", "reverse the heparin", "reverse heparin", "heparin reversal", "protamine", "protamine sulfate", "reverse the lovenox", "reverse lovenox", "reverse the enoxaparin", "reverse enoxaparin", "vitamin k", "phytonadione", "aquamephyton", "iv vitamin k", "po vitamin k", "oral vitamin k", "vitamin k for the inr", "vitamin k for warfarin", "vitamin k for coumadin"]:
    unavailable(p, "Not in the catalog. Reversal here is prothrombin complex concentrate (four-factor PCC) or FFP; the specific reversal agents are not carried.")
alias("intravenous_immunoglobulin", "ivig", "iv ig", "intravenous immunoglobulin", "immunoglobulin", "immune globulin", "gamma globulin", "gammagard", "privigen", "octagam", "flebogamma", "gamunex", "ivig 2 grams per kilo", "ivig 1 gram per kilo", "ivig 0 4 per kilo", "ivig 400 per kilo", "give ivig", "start ivig", "hang ivig", "ivig stat", "ivig now", "immunoglobulin infusion", "ivig infusion", "ivig drip")
alias("factor_viii", "factor 8", "factor eight", "factor viii", "factor 8 concentrate", "factor eight concentrate", "factor viii concentrate", "recombinant factor 8", "recombinant factor eight", "recombinant factor viii", "advate", "kogenate", "humate p", "humate", "alphanate", "koate", "hemofil", "novoeight", "eloctate", "adynovate", "xyntha", "recombinate", "factor 8 replacement", "factor eight replacement", "factor viii replacement", "hemophilia a factor", "hemophilia a factor replacement", "factor for hemophilia a", "50 units per kilo factor 8", "50 units per kilo factor eight", "50 units per kilo factor viii", "factor 8 50 units per kilo", "factor eight 50 units per kilo", "factor viii 50 units per kilo", "25 units per kilo factor 8", "25 units per kilo factor eight", "25 units per kilo factor viii", "factor 8 25 units per kilo", "factor eight 25 units per kilo", "factor viii 25 units per kilo", "give factor 8", "give factor eight", "give factor viii", "factor 8 stat", "factor eight stat", "factor viii stat", "factor 8 now", "factor eight now", "factor viii now", "8 replacement", "eight replacement", "viii replacement")
alias("factor_ix", "factor 9", "factor nine", "factor ix", "factor 9 concentrate", "factor nine concentrate", "factor ix concentrate", "recombinant factor 9", "recombinant factor nine", "recombinant factor ix", "benefix", "alprolix", "idelvion", "rebinyn", "rixubis", "ixinity", "mononine", "alphanine", "factor 9 replacement", "factor nine replacement", "factor ix replacement", "hemophilia b factor", "hemophilia b factor replacement", "factor for hemophilia b", "100 units per kilo factor 9", "100 units per kilo factor nine", "100 units per kilo factor ix", "factor 9 100 units per kilo", "factor nine 100 units per kilo", "factor ix 100 units per kilo", "50 units per kilo factor 9", "50 units per kilo factor nine", "50 units per kilo factor ix", "factor 9 50 units per kilo", "factor nine 50 units per kilo", "factor ix 50 units per kilo", "give factor 9", "give factor nine", "give factor ix", "factor 9 stat", "factor nine stat", "factor ix stat", "factor 9 now", "factor nine now", "factor ix now", "christmas factor", "9 replacement", "nine replacement", "ix replacement")
for p in ["8 replacement", "eight replacement", "viii replacement", "9 replacement", "nine replacement", "ix replacement"]:
    for cid in ("factor_viii", "factor_ix"):
        if p in A[cid]: A[cid].remove(p)
for p in ["factor", "factor replacement", "clotting factor", "clotting factors", "hemophilia factor", "factor concentrate", "give factor", "factor stat", "factor now", "replace factor", "replace the factor", "factor repletion", "replete factor", "replete the factor"]:
    ambiguous(p, "factor_viii", "factor_ix", "prothrombin_complex_concentrate")
for p in ["cryoprecipitate", "cryo", "fibrinogen concentrate", "fibrinogen replacement", "riastap", "fibryga", "fibrinogen", "desmopressin", "ddavp", "von willebrand factor", "vwf", "vwf concentrate", "von willebrand factor concentrate", "vonvendi", "wilate", "novoseven", "recombinant factor vii", "factor vii", "factor viia", "rfviia", "bypassing agent", "bypassing agents", "bypass agent", "bypass agents", "emicizumab", "hemlibra", "feiba", "profilnine", "activated pcc", "apcc", "factor xiii", "antithrombin", "antithrombin 3", "antithrombin iii", "at3", "atiii", "thrombate", "protein c", "protein c concentrate", "ceprotin", "albumin", "5 percent albumin", "25 percent albumin", "albumin 5 percent", "albumin 25 percent", "albumin bolus", "albumin infusion", "colloid", "colloids", "hetastarch", "hespan", "hextend", "dextran", "gelatin", "gelofusine", "voluven", "plasma expander", "plasma expanders", "volume expander", "volume expanders", "granulocytes", "granulocyte transfusion", "white cells", "white cell transfusion", "exchange transfusion", "plasmapheresis", "plasma exchange", "plex", "therapeutic plasma exchange", "tpe", "apheresis", "red cell exchange", "erythrocytapheresis", "leukapheresis", "leukopheresis", "leukoreduction", "leukoreduced", "leukoreduced blood", "irradiated", "irradiated blood", "irradiated products", "cmv negative", "cmv negative blood", "cmv safe", "washed cells", "washed red cells", "washed rbcs", "washed prbcs", "hla matched platelets", "hla matched", "crossmatched platelets", "directed donation", "directed donor", "autologous", "autologous blood", "autologous transfusion", "blood substitute", "blood substitutes", "hemopure", "polyheme", "hemoglobin based oxygen carrier", "hboc", "perfluorocarbon", "perfluorocarbons", "oxygent", "fluosol", "iron", "iv iron", "iron infusion", "iron sucrose", "venofer", "ferumoxytol", "feraheme", "iron dextran", "infed", "ferric carboxymaltose", "injectafer", "ferric gluconate", "ferrlecit", "iron isomaltoside", "monofer", "ferric derisomaltose", "oral iron", "po iron", "ferrous sulfate", "ferrous gluconate", "ferrous fumarate", "epo", "erythropoietin", "epoetin", "epogen", "procrit", "darbepoetin", "aranesp", "esa", "erythropoiesis stimulating agent", "erythropoiesis stimulating agents", "gcsf", "filgrastim", "neupogen", "pegfilgrastim", "neulasta", "sargramostim", "leukine", "tpo", "thrombopoietin", "romiplostim", "nplate", "eltrombopag", "promacta", "avatrombopag", "doptelet", "lusutrombopag", "mulpleta", "il 11", "oprelvekin", "neumega"]:
    unavailable(p, "Not in the catalog. Blood products available: pRBC, FFP, platelets, PCC, factor VIII, factor IX, IVIG.")


# ---------------------------------------------------------------- output
# Every phrase is normalised here with the pipeline above, then deduplicated, so the file
# holds each distinct shape once. Phrases that normalise to nothing are dropped.
DROP_RE = re.compile(r"^(give|some|start) |^(block|inhibit) | (please|stat|now)$| for (the |a |an )?[a-z0-9 ]+$")

def keep(p):
    return bool(p)
def normlist(ps):
    out = []
    for p in ps:
        if DROP_RE.search(p.strip().lower()): continue
        n = normalise(p)
        if n: out.append(n)
    return dedupe(out)

def dedupe(seq):
    out, seen = [], set()
    for x in seq:
        if x not in seen: seen.add(x); out.append(x)
    return out

aliases = {cid: normlist(ps) for cid, ps in A.items()}
aliases = {cid: ps for cid, ps in aliases.items() if ps}
def normmap(d):
    out = {}
    for p, v in d.items():
        if DROP_RE.search(p.strip().lower()): continue
        n = normalise(p)
        if not n: continue
        if n in out and out[n] != v:
            if isinstance(v, list): out[n] = dedupe(out[n] + v)
        else: out[n] = dedupe(v) if isinstance(v, list) else v
    return out
expansions = normmap(EXPAND)
ambig = normmap(AMBIG)
unavail = normmap(UNAVAIL)

# A phrase may live in exactly one table. Ambiguity and expansion win over an alias,
# since they were written on purpose; a phrase in both alias and unavailable is a bug.
owner = {}
CONFLICTS = []
for p in list(expansions): owner[p] = "expansions"
for p in list(ambig):
    if p in owner: print(f"phrase in two tables: {p!r} ({owner[p]}, ambiguous)"); CONFLICTS.append((p,owner[p],"ambiguous"))
    owner[p] = "ambiguous"
for cid, ps in aliases.items():
    for p in ps:
        if p in owner and owner[p] != "alias:" + cid:
            if owner[p].startswith("alias:"):
                CONFLICTS.append((p, owner[p][6:], cid))
            continue
        owner[p] = "alias:" + cid
if CONFLICTS:
    for c in CONFLICTS: print("alias conflict: %r -> %s and %s" % c)
    raise SystemExit(1)
clash=[p for p in unavail if p in owner]
if clash:
    for p in clash: print(f"phrase in two tables: {p!r} ({owner[p]}, unavailable)")
    raise SystemExit(1)
for cid in aliases:
    aliases[cid] = [p for p in aliases[cid] if owner.get(p) == "alias:" + cid]

# Hints repeat across dozens of phrases, so they are stored once and referenced by index.
hints = []
hint_ix = {}
for p_, h in list(unavail.items()):
    if h not in hint_ix: hint_ix[h] = len(hints); hints.append(h)
    unavail[p_] = hint_ix[h]
out = {
    "version": 1,
    "_note": ("Voice order terminology. Generated by catalog/build_voice_aliases.py; edit that, "
              "not this. Keys under aliases are catalog ids. Phrases are normalised by the parser "
              "on load (engine/voice.js) with the pipeline that normalises speech."),
    "normalisation": {"numberWords": NUMBER_WORDS, "canon": CANON, "fillers": sorted(FILLERS), "units": sorted(UNITS)},
    "aliases": aliases,
    "expansions": expansions,
    "ambiguous": ambig,
    "unavailable": unavail,
    "hints": hints,
}
json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
n = sum(len(v) for v in aliases.values())
print(f"wrote {os.path.relpath(OUT)}: {len(aliases)} entries with {n} aliases, "
      f"{len(expansions)} expansions, {len(ambig)} ambiguous, {len(unavail)} unavailable")

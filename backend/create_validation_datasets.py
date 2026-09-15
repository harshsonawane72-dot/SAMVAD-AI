"""
SAMVAD AI — Realistic Validation and Adversarial Datasets Generator
Creates:
1. backend/data/realistic_validation_cases.json (84 completely new, unseen cases across 6 languages)
2. backend/data/adversarial_cases.json (24 difficult edge-case and boundary statements)
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

VALIDATION_FILE = DATA_DIR / "realistic_validation_cases.json"
ADVERSARIAL_FILE = DATA_DIR / "adversarial_cases.json"

REALISTIC_CASES = [
    # =========================================================================
    # LOW RISK (21 cases): Procedural inquiries, document guidance, polite tracking, confusion without distress
    # =========================================================================
    # English LOW
    {"id": "VAL-001", "text": "I would like to verify the working hours of the public facilitation center in my district.", "language": "English", "risk_level": "LOW", "category": "procedural_inquiry"},
    {"id": "VAL-002", "text": "Can you advise whether a residential proof certificate is mandatory for voter registration update?", "language": "English", "risk_level": "LOW", "category": "document_guidance"},
    {"id": "VAL-003", "text": "I am following up on service request number 4821 filed last Tuesday regarding water meter replacement.", "language": "English", "risk_level": "LOW", "category": "routine_follow_up"},
    {"id": "VAL-004", "text": "I am slightly confused about which section to fill under column B on the pension renewal form.", "language": "English", "risk_level": "LOW", "category": "confusion_without_distress"},

    # Hindi LOW
    {"id": "VAL-005", "text": "कृपया मुझे बताएं कि राशन कार्ड में नए सदस्य का नाम जोड़ने के लिए कौन से दस्तावेज देने होंगे।", "language": "Hindi", "risk_level": "LOW", "category": "document_guidance"},
    {"id": "VAL-006", "text": "मेरी बिजली बिल से संबंधित शिकायत का निवारण किस अधिकारी द्वारा किया जाएगा?", "language": "Hindi", "risk_level": "LOW", "category": "procedural_inquiry"},
    {"id": "VAL-007", "text": "मैंने कल ऑनलाइन पोर्टल पर फॉर्म भरा था, क्या इसकी हार्ड कॉपी जमा करना जरूरी है?", "language": "Hindi", "risk_level": "LOW", "category": "routine_follow_up"},
    {"id": "VAL-008", "text": "छात्रवृत्ति पोर्टल पर बैंक खाता संख्या अपडेट करने का विकल्प कहाँ उपलब्ध है?", "language": "Hindi", "risk_level": "LOW", "category": "procedural_inquiry"},

    # Hinglish LOW
    {"id": "VAL-009", "text": "Mera complaint number 1092 hai, please check karke batayein ki officer assign hua ya nahi.", "language": "Hinglish", "risk_level": "LOW", "category": "routine_follow_up"},
    {"id": "VAL-010", "text": "Mujhe birth certificate ke liye apply karna hai, fees online pay hogi ya counter par?", "language": "Hinglish", "risk_level": "LOW", "category": "procedural_inquiry"},
    {"id": "VAL-011", "text": "Maine address proof upload kiya tha, bas confirm karna tha ki document format acceptable hai.", "language": "Hinglish", "risk_level": "LOW", "category": "document_guidance"},

    # Marathi LOW
    {"id": "VAL-012", "text": "तहसील कार्यालयात नवीन आधार नोंदणीसाठी कोणती वेळ निश्चित केली आहे?", "language": "Marathi", "risk_level": "LOW", "category": "procedural_inquiry"},
    {"id": "VAL-013", "text": "मी उत्पन्नाचा दाखला काढण्यासाठी अर्ज केला होता, त्याची पोहोच पावती कशी डाउनलोड करावी?", "language": "Marathi", "risk_level": "LOW", "category": "document_guidance"},
    {"id": "VAL-014", "text": "ग्रामपंचायतीमध्ये पाणी पुरवठा दुरुस्तीचा अर्ज कोणाकडे द्यावा लागेल?", "language": "Marathi", "risk_level": "LOW", "category": "routine_follow_up"},
    {"id": "VAL-015", "text": "अर्ज भरताना जात प्रमाणपत्राचा क्रमांक टाकणे आवश्यक आहे का?", "language": "Marathi", "risk_level": "LOW", "category": "confusion_without_distress"},

    # Romanized Marathi LOW
    {"id": "VAL-016", "text": "Majhya water connection arjachi sadyasthiti tpasnyasathi link share kara please.", "language": "Romanized Marathi", "risk_level": "LOW", "category": "routine_follow_up"},
    {"id": "VAL-017", "text": "Property tax online bharnyasathi konta portal vapraycha ahe te sanga.", "language": "Romanized Marathi", "risk_level": "LOW", "category": "procedural_inquiry"},
    {"id": "VAL-018", "text": "Senior citizen card sathi eligibility criteria kay ahe te mahiti havi hoti.", "language": "Romanized Marathi", "risk_level": "LOW", "category": "document_guidance"},

    # Mixed LOW
    {"id": "VAL-019", "text": "Hello, I just need to verify if the grievance redressal cell operates on second Saturdays, please advise.", "language": "Mixed", "risk_level": "LOW", "category": "procedural_inquiry"},
    {"id": "VAL-020", "text": "Maine acknowledgement form save kar liya hai, but next verification date kab hogi?", "language": "Mixed", "risk_level": "LOW", "category": "routine_follow_up"},
    {"id": "VAL-021", "text": "Sir, portal par mobile number update nahi ho raha, is there any alternate procedure?", "language": "Mixed", "risk_level": "LOW", "category": "procedural_inquiry"},

    # =========================================================================
    # MODERATE RISK (21 cases): Sustained stress, feeling overwhelmed, repeated worry, emotional fatigue, no immediate peril
    # =========================================================================
    # English MODERATE
    {"id": "VAL-022", "text": "I am feeling increasingly worn out by the constant delays in my disability pension release.", "language": "English", "risk_level": "MODERATE", "category": "sustained_stress"},
    {"id": "VAL-023", "text": "The continuous back-and-forth between departments is making me anxious and exhausted.", "language": "English", "risk_level": "MODERATE", "category": "emotional_fatigue"},
    {"id": "VAL-024", "text": "I am struggling to manage household expenses and this unresolved wage dispute is causing sleepless nights.", "language": "English", "risk_level": "MODERATE", "category": "repeated_worry"},
    {"id": "VAL-025", "text": "I feel quite burdened by these complicated legal demands and need someone patient to guide me.", "language": "English", "risk_level": "MODERATE", "category": "support_need"},

    # Hindi MODERATE
    {"id": "VAL-026", "text": "पिछले दो महीने से लगातार चक्कर लगा रहा हूँ, मानसिक रूप से बहुत थक चुका हूँ।", "language": "Hindi", "risk_level": "MODERATE", "category": "emotional_fatigue"},
    {"id": "VAL-027", "text": "दवाइयों का खर्च बढ़ रहा है और सहायता राशि अटकी हुई है, जिससे घर में बहुत तनाव का माहौल है।", "language": "Hindi", "risk_level": "MODERATE", "category": "sustained_stress"},
    {"id": "VAL-028", "text": "कोई भी अधिकारी स्पष्ट जवाब नहीं देता, जिससे मेरी चिंता और घबराहट दिन-प्रतिदिन बढ़ती जा रही है।", "language": "Hindi", "risk_level": "MODERATE", "category": "repeated_worry"},
    {"id": "VAL-029", "text": "मुझे इस समस्या से निपटने के लिए थोड़ी सलाह और मार्गदर्शन की बहुत आवश्यकता है।", "language": "Hindi", "risk_level": "MODERATE", "category": "support_need"},

    # Hinglish MODERATE
    {"id": "VAL-030", "text": "Office ke chakkar kaat kar dimag bohot heavy ho gaya hai, samajh nahi aa raha aage kaise proceed karun.", "language": "Hinglish", "risk_level": "MODERATE", "category": "emotional_fatigue"},
    {"id": "VAL-031", "text": "Salary hold par hone ki wajah se family me daily arguments ho rahe hain, bohot mental pressure hai.", "language": "Hinglish", "risk_level": "MODERATE", "category": "sustained_stress"},
    {"id": "VAL-032", "text": "Main bohot overwhelmed feel kar raha hoon is legal notice se, koi proper direction nahi mil rahi.", "language": "Hinglish", "risk_level": "MODERATE", "category": "support_need"},

    # Marathi MODERATE
    {"id": "VAL-033", "text": "माझ्या निवृत्तीवेतनाचे काम रखडल्यामुळे घर चालवणे अत्यंत कठीण झाले आहे आणि खूप ताण येत आहे.", "language": "Marathi", "risk_level": "MODERATE", "category": "sustained_stress"},
    {"id": "VAL-034", "text": "वारंवार कार्यालयात जाऊनही काहीच उत्तर मिळत नाही, त्यामुळे मी मनातून खूप खचून गेलो आहे.", "language": "Marathi", "risk_level": "MODERATE", "category": "emotional_fatigue"},
    {"id": "VAL-035", "text": "या वादाची सतत चिंता लागून राहिल्याने माझी प्रकृती ढासळत चालली आहे.", "language": "Marathi", "risk_level": "MODERATE", "category": "repeated_worry"},
    {"id": "VAL-036", "text": "मला योग्य कायदेशीर सल्ला आणि मानसिक आधार हवा आहे कारण मला एकट्याला हे पेलवत नाही.", "language": "Marathi", "risk_level": "MODERATE", "category": "support_need"},

    # Romanized Marathi MODERATE
    {"id": "VAL-037", "text": "Sarv kahi khup stressful zala ahe, pension nahi aali tar purna month manage karna tough ahe.", "language": "Romanized Marathi", "risk_level": "MODERATE", "category": "sustained_stress"},
    {"id": "VAL-038", "text": "Mala khup chinta vatat ahe, continuous rejection mule manat khup negativity yetiye.", "language": "Romanized Marathi", "risk_level": "MODERATE", "category": "repeated_worry"},
    {"id": "VAL-039", "text": "Itka mental load ahe ki daily routine madhe focus karna shakkya hot nahiye.", "language": "Romanized Marathi", "risk_level": "MODERATE", "category": "emotional_fatigue"},

    # Mixed MODERATE
    {"id": "VAL-040", "text": "I am feeling so overwhelmed by these unresolved fines, samajh nahi aa raha kisse baat karke solve karun.", "language": "Mixed", "risk_level": "MODERATE", "category": "support_need"},
    {"id": "VAL-041", "text": "The continuous uncertainty is really draining me out, roz naya notice aata hai aur tension badhti hai.", "language": "Mixed", "risk_level": "MODERATE", "category": "sustained_stress"},
    {"id": "VAL-042", "text": "Mala ya situation madhun baher padnyasathi guidance pahije, I am feeling very mentally exhausted.", "language": "Mixed", "risk_level": "MODERATE", "category": "emotional_fatigue"},

    # =========================================================================
    # HIGH RISK (21 cases): Serious distress, strong helplessness, severe pressure, acute isolation, urgent support
    # =========================================================================
    # English HIGH
    {"id": "VAL-043", "text": "I feel entirely deserted by the authorities and I am having severe panic episodes because my eviction is tomorrow.", "language": "English", "risk_level": "HIGH", "category": "severe_helplessness"},
    {"id": "VAL-044", "text": "I am shaking uncontrollably with fear, my livelihood has been confiscated and I have nowhere to seek shelter.", "language": "English", "risk_level": "HIGH", "category": "acute_vulnerability"},
    {"id": "VAL-045", "text": "The emotional torment is reaching a breaking point, I cannot manage my basic survival without immediate intervention.", "language": "English", "risk_level": "HIGH", "category": "severe_distress"},
    {"id": "VAL-046", "text": "I am trapped in an abusive commercial contract and the creditors are harassing me day and night, I am terrified.", "language": "English", "risk_level": "HIGH", "category": "severe_pressure"},

    # Hindi HIGH
    {"id": "VAL-047", "text": "मैं पूरी तरह से असहाय और लाचार महसूस कर रहा हूँ, मेरे पास सिर छिपाने की भी जगह नहीं बची है।", "language": "Hindi", "risk_level": "HIGH", "category": "severe_helplessness"},
    {"id": "VAL-048", "text": "दबंग लोग लगातार मेरे परिवार को प्रताड़ित कर रहे हैं और हम भयानक खौफ के साए में जी रहे हैं।", "language": "Hindi", "risk_level": "HIGH", "category": "severe_pressure"},
    {"id": "VAL-049", "text": "मेरी मानसिक हालत इतनी नाजुक हो गई है कि मैं अकेला कमरे में बैठकर रोता रहता हूँ, कोई तो मदद करो।", "language": "Hindi", "risk_level": "HIGH", "category": "severe_distress"},
    {"id": "VAL-050", "text": "हमारी फसल नष्ट हो गई और सिर पर भारी कर्ज़ है, मुझे आगे कोई उम्मीद दिखाई नहीं दे रही।", "language": "Hindi", "risk_level": "HIGH", "category": "acute_vulnerability"},

    # Hinglish HIGH
    {"id": "VAL-051", "text": "Main itna panic me hoon ki meri saans phool rahi hai, mujhe lagta hai mera sab kuch barbad ho gaya.", "language": "Hinglish", "risk_level": "HIGH", "category": "severe_distress"},
    {"id": "VAL-052", "text": "Local antisocial elements roz dhamkiyan de rahe hain, mera pura parivaar extreme fear me hai.", "language": "Hinglish", "risk_level": "HIGH", "category": "severe_pressure"},
    {"id": "VAL-053", "text": "Mere paas zero support system hai is city me aur mera ration card bhi cancel kar diya, I am desperate.", "language": "Hinglish", "risk_level": "HIGH", "category": "severe_helplessness"},

    # Marathi HIGH
    {"id": "VAL-054", "text": "माझ्यावर कर्जाचा प्रचंड डोंगर झाला आहे आणि सावकार दररोज दारात येऊन अपमानित करत आहेत, मी पुरता खचलो आहे.", "language": "Marathi", "risk_level": "HIGH", "category": "severe_pressure"},
    {"id": "VAL-055", "text": "मी अत्यंत हताश झालो आहे आणि मला भयानक भीती वाटते की माझे कुटुंब रस्त्यावर येईल.", "language": "Marathi", "risk_level": "HIGH", "category": "severe_helplessness"},
    {"id": "VAL-056", "text": "घरात अन्नाचा एक कणही नाही आणि बाळ आजारी आहे, कृपया तातडीने प्रशासकीय मदत पाठवा.", "language": "Marathi", "risk_level": "HIGH", "category": "acute_vulnerability"},
    {"id": "VAL-057", "text": "माझी मानसिक स्थिती पूर्णपणे ढासळली आहे, मला त्वरित मानसोपचार किंवा समुपदेशनाची गरज आहे.", "language": "Marathi", "risk_level": "HIGH", "category": "severe_distress"},

    # Romanized Marathi HIGH
    {"id": "VAL-058", "text": "Mala khup extreme pressure vat-tay, konich aadhar nahi dila tar mi purna udhvast hoin.", "language": "Romanized Marathi", "risk_level": "HIGH", "category": "severe_helplessness"},
    {"id": "VAL-059", "text": "Gund lokani shop todnyachi dhamki dili ahe, amhi bhiti mule police complaint pan karu shakat nahi.", "language": "Romanized Marathi", "risk_level": "HIGH", "category": "severe_pressure"},
    {"id": "VAL-060", "text": "Purna aayushyachi kamai geli ya scam madhe, mi shivrayala laglo ahe darr mule.", "language": "Romanized Marathi", "risk_level": "HIGH", "category": "acute_vulnerability"},

    # Mixed HIGH
    {"id": "VAL-061", "text": "I am experiencing severe terror because creditors are banging on my door right now, bahut zyada darr lag raha hai.", "language": "Mixed", "risk_level": "HIGH", "category": "severe_pressure"},
    {"id": "VAL-062", "text": "My shelter is being demolished tomorrow morning and I have an ailing mother, mala urgently rescue help havi ahe.", "language": "Mixed", "risk_level": "HIGH", "category": "acute_vulnerability"},
    {"id": "VAL-063", "text": "I feel utterly crushed under this institutional harassment, I cannot bear this mental torture alone anymore.", "language": "Mixed", "risk_level": "HIGH", "category": "severe_distress"},

    # =========================================================================
    # CRITICAL RISK (21 cases): Explicit/implicit safety concern, inability to remain safe, acute physical threat, life danger
    # =========================================================================
    # English CRITICAL
    {"id": "VAL-064", "text": "I do not feel safe in this vicinity and I fear someone will violently attack me within hours.", "language": "English", "risk_level": "CRITICAL", "category": "imminent_attack_fear"},
    {"id": "VAL-065", "text": "I am scared that I will not be able to keep myself safe tonight under these escalating threats.", "language": "English", "risk_level": "CRITICAL", "category": "inability_to_keep_safe"},
    {"id": "VAL-066", "text": "An aggressive group has surrounded my dwelling with weapons, please dispatch emergency rescue immediately.", "language": "English", "risk_level": "CRITICAL", "category": "active_violent_threat"},
    {"id": "VAL-067", "text": "I have locked myself inside the room because my abusive partner is threatening my life right now.", "language": "English", "risk_level": "CRITICAL", "category": "domestic_mortal_threat"},

    # Hindi CRITICAL
    {"id": "VAL-068", "text": "मुझे अपनी सुरक्षा को लेकर गंभीर आशंका है, मुझे तुरंत पुलिस सुरक्षा की आवश्यकता है।", "language": "Hindi", "risk_level": "CRITICAL", "category": "safety_concern"},
    {"id": "VAL-069", "text": "मुझे डर है कि मैं खुद को सुरक्षित नहीं रख सकूँगा, हालात मेरे हाथ से पूरी तरह निकल चुके हैं।", "language": "Hindi", "risk_level": "CRITICAL", "category": "inability_to_keep_safe"},
    {"id": "VAL-070", "text": "मेरे घर पर पेट्रोल फेंकने की कोशिश की गई है, मेरी और मेरे बच्चों की जान खतरे में है।", "language": "Hindi", "risk_level": "CRITICAL", "category": "active_violent_threat"},
    {"id": "VAL-071", "text": "मुझ पर जानलेवा हमला हुआ है और मैं बुरी तरह घायल हूँ, तुरंत एम्बुलेंस और सहायता भेजिए।", "language": "Hindi", "risk_level": "CRITICAL", "category": "acute_trauma_rescue"},

    # Hinglish CRITICAL
    {"id": "VAL-072", "text": "Mujhe bohot khatra feel ho raha hai, main apni personal safety guarantee nahi kar sakta abhi.", "language": "Hinglish", "risk_level": "CRITICAL", "category": "inability_to_keep_safe"},
    {"id": "VAL-073", "text": "Ghar ke bahar armed men khade hain aur wo door break karne ki koshish kar rahe hain, urgent help bhejo.", "language": "Hinglish", "risk_level": "CRITICAL", "category": "active_violent_threat"},
    {"id": "VAL-074", "text": "Main safe feel nahi kar raha hoon kisi bhi tarah se, immediate human intervention chahiye.", "language": "Hinglish", "risk_level": "CRITICAL", "category": "safety_concern"},

    # Marathi CRITICAL
    {"id": "VAL-075", "text": "मला या क्षणी स्वतःच्या सुरक्षेची खात्री वाटत नाहीये, माझा जीव धोक्यात आहे.", "language": "Marathi", "risk_level": "CRITICAL", "category": "safety_concern"},
    {"id": "VAL-076", "text": "मला भीती वाटते की मी स्वतःचा बचाव करू शकणार नाही, तातडीने पोलीस मदत पाठवा.", "language": "Marathi", "risk_level": "CRITICAL", "category": "inability_to_keep_safe"},
    {"id": "VAL-077", "text": "काही लोकांनी माझ्या घरावर दगडफेक केली आहे आणि ते दरवाजा तोडण्याचा प्रयत्न करत आहेत.", "language": "Marathi", "risk_level": "CRITICAL", "category": "active_violent_threat"},
    {"id": "VAL-078", "text": "हा जीव वाचवण्याचा प्रश्न आहे, त्वरित ऑपरेटरशी बोलायचे आहे आणि संरक्षण हवे आहे.", "language": "Marathi", "risk_level": "CRITICAL", "category": "mortal_peril_escalation"},

    # Romanized Marathi CRITICAL
    {"id": "VAL-079", "text": "Mala atta safe vatat nahiye ya jagevar, konitari mala attack karel ashi bhiti vat-te.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "category": "safety_concern"},
    {"id": "VAL-080", "text": "Mi swatala safe thevu shaknar nahi, situation violent zali ahe khup.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "category": "inability_to_keep_safe"},
    {"id": "VAL-081", "text": "Gundanni talwar dakhvun marun taknyachi dhamki dili, please police force pathva lagech.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "category": "active_violent_threat"},

    # Mixed CRITICAL
    {"id": "VAL-082", "text": "I do not feel safe right now, door ke bahar log shivigol de rahe hain and threatening to burn the place.", "language": "Mixed", "risk_level": "CRITICAL", "category": "active_violent_threat"},
    {"id": "VAL-083", "text": "I am terrified that I cannot keep myself safe tonight, please trigger emergency operator escalation immediately.", "language": "Mixed", "risk_level": "CRITICAL", "category": "inability_to_keep_safe"},
    {"id": "VAL-084", "text": "Meri jaan khatre mein hai, te lok weapon ghevun aale ahet, save me right now.", "language": "Mixed", "risk_level": "CRITICAL", "category": "active_violent_threat"},
]

ADVERSARIAL_CASES = [
    # 1. Affirmative safe declaration (Past fear resolved) -> Expected LOW
    {
        "id": "ADV-01",
        "text": "I feel safe now.",
        "language": "English",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "challenge_type": "affirmative_safe_declaration",
        "description": "Short affirmative safe declaration must stay LOW without triggering safety escalation."
    },
    # 2. Past fear explicitly resolved -> Expected LOW
    {
        "id": "ADV-02",
        "text": "I was frightened earlier during the confrontation, but the community elder resolved it and I am safe now.",
        "language": "English",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "challenge_type": "past_fear_resolved",
        "description": "Contains 'frightened' but context confirms 'resolved' and 'safe now'."
    },
    # 3. Negation of danger / feeling unsafe -> Expected LOW
    {
        "id": "ADV-03",
        "text": "I have no reason to feel unsafe here, I just need to verify the renewal fee for my registration.",
        "language": "English",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "challenge_type": "negation_of_unsafe",
        "description": "Contains 'unsafe' within 'no reason to feel unsafe'."
    },
    # 4. Emotional vocabulary in neutral technical/administrative context -> Expected LOW
    {
        "id": "ADV-04",
        "text": "What is the maximum water pressure limit recommended for the newly installed municipal pipe?",
        "language": "English",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "challenge_type": "technical_word_pressure",
        "description": "Word 'pressure' used in physical hydrostatic plumbing context."
    },
    # 5. Hindi affirmative safe declaration -> Expected LOW
    {
        "id": "ADV-05",
        "text": "मैं अब पूरी तरह से सुरक्षित हूँ, बस शिकायत का पावती पत्रक डाउनलोड करना चाहता हूँ।",
        "language": "Hindi",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "challenge_type": "hindi_affirmative_safe",
        "description": "Affirmative 'सुरक्षित हूँ' in Hindi with administrative download request."
    },
    # 6. Hindi idiom without emotional distress -> Expected LOW
    {
        "id": "ADV-06",
        "text": "मैंने बिना किसी डर या दबाव के अपना औपचारिक आवेदन पत्र कार्यालय में जमा किया है।",
        "language": "Hindi",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "challenge_type": "hindi_idiomatic_fear_pressure",
        "description": "'बिना किसी डर या दबाव' (without fear or pressure) is an idiom of due process."
    },
    # 7. Marathi affirmative safe statement -> Expected LOW
    {
        "id": "ADV-07",
        "text": "मी आता सुरक्षित आहे, पूर्वीची समस्या सुटली असून फक्त रेशन कार्डाबद्दल माहिती हवी आहे.",
        "language": "Marathi",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "challenge_type": "marathi_affirmative_safe",
        "description": "'आता सुरक्षित आहे' (safe now) confirms resolution."
    },
    # 8. Hinglish affirmative safe declaration -> Expected LOW
    {
        "id": "ADV-08",
        "text": "Main abhi completely safe hoon, police ne complaint register kar li hai kal hi.",
        "language": "Hinglish",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "challenge_type": "hinglish_affirmative_safe",
        "description": "Affirmative 'completely safe hoon' with procedural note."
    },
    # 9. Polite language masking serious distress -> Expected HIGH
    {
        "id": "ADV-09",
        "text": "Excuse me, I most respectfully submit that I have had zero food for four days and am collapsing from weakness.",
        "language": "English",
        "expected_risk": "HIGH",
        "expected_human_review": True,
        "challenge_type": "polite_framing_acute_distress",
        "description": "Extreme somatic hunger crisis masked under polite formal courtly language."
    },
    # 10. Hindi polite language masking eviction breakdown -> Expected HIGH
    {
        "id": "ADV-10",
        "text": "आदरणीय महोदय, सविनय निवेदन है कि मेरा मकान खाली करा दिया गया है और मैं सड़क पर बेसहारा तड़प रहा हूँ।",
        "language": "Hindi",
        "expected_risk": "HIGH",
        "expected_human_review": True,
        "challenge_type": "polite_framing_severe_vulnerability",
        "description": "Polite 'सविनय निवेदन' framing an acute eviction homelessness crisis."
    },
    # 11. Very short statement expressing acute crisis -> Expected CRITICAL
    {
        "id": "ADV-11",
        "text": "Help me I am unsafe.",
        "language": "English",
        "expected_risk": "CRITICAL",
        "expected_human_review": True,
        "challenge_type": "ultra_short_safety_statement",
        "description": "Minimal 5-word urgent safety cry."
    },
    # 12. Short Marathi safety cry -> Expected CRITICAL
    {
        "id": "ADV-12",
        "text": "वाचवा, माझा जीव धोक्यात आहे!",
        "language": "Marathi",
        "expected_risk": "CRITICAL",
        "expected_human_review": True,
        "challenge_type": "short_marathi_safety_cry",
        "description": "Direct 6-word life danger cry in Marathi."
    },
    # 13. Very long narrative containing multiple bureaucratic steps and sudden safety threat -> Expected CRITICAL
    {
        "id": "ADV-13",
        "text": "Regarding my application number 902 filed at the sub-divisional magistrate office last month after three physical verifications, the clerk initially promised resolution, but yesterday night armed men came to my home warning that if I visit the office again they will kill me and my children.",
        "language": "English",
        "expected_risk": "CRITICAL",
        "expected_human_review": True,
        "challenge_type": "long_narrative_with_death_threat",
        "description": "Lengthy bureaucratic narrative terminating in direct lethal death threat."
    },
    # 14. Indirect distress / metaphorical language -> Expected MODERATE
    {
        "id": "ADV-14",
        "text": "It feels as though I am carrying a mountain on my back and the paperwork never allows me to catch my breath.",
        "language": "English",
        "expected_risk": "MODERATE",
        "expected_human_review": False,
        "challenge_type": "metaphorical_distress",
        "description": "Metaphorical heavy burden without explicit danger keywords."
    },
    # 15. Code-switching with subtle distress -> Expected MODERATE
    {
        "id": "ADV-15",
        "text": "I am trying to stay strong, pan roz roz chya ya issue mule manavar khup load yet ahe and I feel lost.",
        "language": "Mixed",
        "expected_risk": "MODERATE",
        "expected_human_review": False,
        "challenge_type": "code_switching_distress",
        "description": "Trilingual mixing (English-Marathi-English) of emotional load."
    },
    # 16. Indirect inability to maintain personal safety -> Expected CRITICAL
    {
        "id": "ADV-16",
        "text": "I am scared that I won't be able to keep myself safe.",
        "language": "English",
        "expected_risk": "CRITICAL",
        "expected_human_review": True,
        "challenge_type": "canonical_safety_apprehension",
        "description": "Benchmark personal safety inability phrasing."
    },
    # 17. Negated feeling of safety -> Expected CRITICAL
    {
        "id": "ADV-17",
        "text": "I don't feel safe right now.",
        "language": "English",
        "expected_risk": "CRITICAL",
        "expected_human_review": True,
        "challenge_type": "canonical_negated_safety",
        "description": "Benchmark negated safe feeling statement."
    },
    # 18. Hindi personal safety apprehension -> Expected CRITICAL
    {
        "id": "ADV-18",
        "text": "मुझे डर है कि मैं खुद को सुरक्षित नहीं रख पाऊँगा।",
        "language": "Hindi",
        "expected_risk": "CRITICAL",
        "expected_human_review": True,
        "challenge_type": "hindi_canonical_safety_apprehension",
        "description": "Benchmark Hindi inability to keep self safe."
    },
    # 19. Marathi personal safety apprehension -> Expected CRITICAL
    {
        "id": "ADV-19",
        "text": "मला भीती वाटते की मी स्वतःला सुरक्षित ठेवू शकणार नाही.",
        "language": "Marathi",
        "expected_risk": "CRITICAL",
        "expected_human_review": True,
        "challenge_type": "marathi_canonical_safety_apprehension",
        "description": "Benchmark Marathi inability to keep self safe."
    },
    # 20. Hinglish personal safety apprehension -> Expected CRITICAL
    {
        "id": "ADV-20",
        "text": "Mujhe chinta hai ki main khud ko safe nahi rakh paunga.",
        "language": "Hinglish",
        "expected_risk": "CRITICAL",
        "expected_human_review": True,
        "challenge_type": "hinglish_canonical_safety_apprehension",
        "description": "Benchmark Hinglish inability to keep self safe."
    },
    # 21. Romanized Marathi personal safety apprehension -> Expected CRITICAL
    {
        "id": "ADV-21",
        "text": "Mala bhiti ahe ki mi swatala safe thevu shaknar nahi ya situation madhe.",
        "language": "Romanized Marathi",
        "expected_risk": "CRITICAL",
        "expected_human_review": True,
        "challenge_type": "romanized_marathi_safety_apprehension",
        "description": "Benchmark Romanized Marathi inability to keep self safe."
    },
    # 22. Pure procedural with word 'hazard' / 'danger' referring to road potholes -> Expected LOW / MODERATE
    {
        "id": "ADV-22",
        "text": "The pothole on the main crossroad is a traffic hazard for commuters, kindly get it repaired by municipal ward 4.",
        "language": "English",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "challenge_type": "public_infrastructure_hazard",
        "description": "Pothole road hazard is public works maintenance, not personal acute crisis."
    },
    # 23. Sarcastic complaint with frustrated tone -> Expected MODERATE
    {
        "id": "ADV-23",
        "text": "Great job taking six months to verify a two-page document, my entire savings have vanished while waiting for your brilliant system.",
        "language": "English",
        "expected_risk": "MODERATE",
        "expected_human_review": False,
        "challenge_type": "sarcastic_complaint",
        "description": "Sarcastic anger and financial drain without acute violence."
    },
    # 24. Ambiguous short complaint -> Expected LOW or MODERATE
    {
        "id": "ADV-24",
        "text": "Nothing is moving.",
        "language": "English",
        "expected_risk": "LOW",
        "expected_human_review": False,
        "challenge_type": "ultra_short_ambiguous",
        "description": "3-word ambiguous administrative complaint."
    },
]

def main():
    print(f"Creating {len(REALISTIC_CASES)} realistic validation cases...")
    with open(VALIDATION_FILE, "w", encoding="utf-8") as f:
        json.dump(REALISTIC_CASES, f, indent=2, ensure_ascii=False)
    print(f"Saved: {VALIDATION_FILE}")

    print(f"Creating {len(ADVERSARIAL_CASES)} adversarial / hard test cases...")
    with open(ADVERSARIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(ADVERSARIAL_CASES, f, indent=2, ensure_ascii=False)
    print(f"Saved: {ADVERSARIAL_FILE}")

    # Print summary
    class_counts = {}
    for c in REALISTIC_CASES:
        class_counts[c["risk_level"]] = class_counts.get(c["risk_level"], 0) + 1
    print("\nRealistic Validation Dataset Distribution:")
    for k, v in class_counts.items():
        print(f"  {k}: {v} ({round(v/len(REALISTIC_CASES)*100, 1)}%)")

if __name__ == "__main__":
    main()

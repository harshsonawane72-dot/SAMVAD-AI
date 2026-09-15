"""
Script to create the curated benchmark dataset for SAMVAD AI risk classification.
Target: 264 natural, human-style complaints balanced across LOW, MODERATE, HIGH, CRITICAL
across 6 linguistic variations: English, Hindi, Hinglish, Marathi, Romanized Marathi, Mixed.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "complaints_dataset.json"

RAW_DATA = [
    # =========================================================================
    # LOW RISK (~66 examples): Procedural questions, status inquiries, document help, polite requests
    # =========================================================================
    # English LOW
    {"text": "I want to know the status of my complaint filed last week.", "language": "English", "risk_level": "LOW", "reason": "Standard status tracking request."},
    {"text": "Could you please explain what documents are required for the scholarship verification?", "language": "English", "risk_level": "LOW", "reason": "Procedural documentation inquiry."},
    {"text": "I submitted my grievance regarding pension delay and need an update.", "language": "English", "risk_level": "LOW", "reason": "Administrative inquiry without distress."},
    {"text": "Where can I find the official guidelines for filing an appeal?", "language": "English", "risk_level": "LOW", "reason": "Information seeking about procedure."},
    {"text": "Is there any contact number for the district welfare office?", "language": "English", "risk_level": "LOW", "reason": "Contact directory request."},
    {"text": "I made an error in my application form. How do I correct it?", "language": "English", "risk_level": "LOW", "reason": "Form correction guidance."},
    {"text": "Please confirm if my submitted papers have reached the department.", "language": "English", "risk_level": "LOW", "reason": "Verification receipt confirmation."},
    {"text": "What is the usual processing time for municipal water complaints?", "language": "English", "risk_level": "LOW", "reason": "Service timeline question."},
    {"text": "I am feeling fine now and just checking on my application progress.", "language": "English", "risk_level": "LOW", "reason": "Safe affirmation with administrative check."},
    {"text": "Can someone guide me on how to register on the national portal?", "language": "English", "risk_level": "LOW", "reason": "Portal navigation support."},
    {"text": "My electricity meter reading seems higher than expected, whom should I contact?", "language": "English", "risk_level": "LOW", "reason": "Billing procedural query."},

    # Hindi LOW
    {"text": "मुझे अपनी शिकायत की वर्तमान स्थिति जाननी है।", "language": "Hindi", "risk_level": "LOW", "reason": "Standard complaint status inquiry in Hindi."},
    {"text": "कृपया बताएं कि आवेदन के लिए कौन से दस्तावेज आवश्यक हैं।", "language": "Hindi", "risk_level": "LOW", "reason": "Documentation requirements inquiry."},
    {"text": "मैंने कल अपनी पेंशन का फॉर्म जमा किया था, पावती कैसे मिलेगी?", "language": "Hindi", "risk_level": "LOW", "reason": "Receipt tracking inquiry."},
    {"text": "पोर्टल पर नया खाता कैसे बनाएं, इसकी जानकारी चाहिए।", "language": "Hindi", "risk_level": "LOW", "reason": "Account creation guidance."},
    {"text": "क्या शिकायत निवारण अधिकारी का संपर्क नंबर मिल सकता है?", "language": "Hindi", "risk_level": "LOW", "reason": "Officer contact details request."},
    {"text": "राशन कार्ड में नाम सुधारने की प्रक्रिया क्या है?", "language": "Hindi", "risk_level": "LOW", "reason": "Name correction procedure."},
    {"text": "मैं अभी बिल्कुल ठीक हूँ, बस आवेदन संख्या जानना चाहता हूँ।", "language": "Hindi", "risk_level": "LOW", "reason": "Affirmative safe statement with inquiry."},
    {"text": "तहसील कार्यालय का कार्य समय क्या होता है?", "language": "Hindi", "risk_level": "LOW", "reason": "Office timing inquiry."},
    {"text": "छात्रवृत्ति की अगली किस्त कब तक आने की संभावना है?", "language": "Hindi", "risk_level": "LOW", "reason": "Scholarship disbursement inquiry."},
    {"text": "ऑनलाइन शिकायत दर्ज करने में सहायता चाहिए।", "language": "Hindi", "risk_level": "LOW", "reason": "Online filing assistance request."},
    {"text": "मेरे गाँव में सड़क मरम्मत का काम कब शुरू होगा?", "language": "Hindi", "risk_level": "LOW", "reason": "Infrastructure schedule inquiry."},

    # Hinglish LOW
    {"text": "Mujhe apni complaint ke process ke baare mein information chahiye.", "language": "Hinglish", "risk_level": "LOW", "reason": "Complaint process inquiry in Hinglish."},
    {"text": "Maine jo documents upload kiye the wo verify hue ya nahi?", "language": "Hinglish", "risk_level": "LOW", "reason": "Document verification check."},
    {"text": "Application reference number track karne ka link share kar dijiye.", "language": "Hinglish", "risk_level": "LOW", "reason": "Tracking link request."},
    {"text": "Kya main kal subah office aakar apna form submit kar sakta hoon?", "language": "Hinglish", "risk_level": "LOW", "reason": "Submission appointment check."},
    {"text": "Mera registration certificate kab tak download hoga?", "language": "Hinglish", "risk_level": "LOW", "reason": "Certificate download status."},
    {"text": "Sab kuch theek hai, bas mujhe helpline number confirm karna tha.", "language": "Hinglish", "risk_level": "LOW", "reason": "Safe statement with helpline check."},
    {"text": "Naya ration card apply karne ke rules batayein please.", "language": "Hinglish", "risk_level": "LOW", "reason": "Scheme rules inquiry."},
    {"text": "Portal par error aa raha hai login karte samay.", "language": "Hinglish", "risk_level": "LOW", "reason": "Technical login issue."},
    {"text": "Electricity bill payment update nahi hua hai portal par.", "language": "Hinglish", "risk_level": "LOW", "reason": "Payment update check."},
    {"text": "Grievance redressal officer ka cabin kaun se floor par hai?", "language": "Hinglish", "risk_level": "LOW", "reason": "Office location inquiry."},
    {"text": "Mujhe scholarship form ka printout lena hai.", "language": "Hinglish", "risk_level": "LOW", "reason": "Printout guidance inquiry."},

    # Marathi LOW
    {"text": "माझ्या अर्जाची सद्यस्थिती काय आहे हे मला जाणून घ्यायचे आहे.", "language": "Marathi", "risk_level": "LOW", "reason": "Standard status check in Marathi."},
    {"text": "नवीन रेशन कार्ड काढण्यासाठी कोणती कागदपत्रे लागतील?", "language": "Marathi", "risk_level": "LOW", "reason": "Document requirements inquiry."},
    {"text": "मी काल तक्रार नोंदवली होती, त्याचा संदर्भ क्रमांक कसा तपासायचा?", "language": "Marathi", "risk_level": "LOW", "reason": "Reference number tracking."},
    {"text": "तालुका कार्यालयात संपर्क साधण्यासाठी दूरध्वनी क्रमांक मिळेल का?", "language": "Marathi", "risk_level": "LOW", "reason": "Office telephone request."},
    {"text": "पाणी पुरवठा विभागाची तक्रार निवारण वेळ काय आहे?", "language": "Marathi", "risk_level": "LOW", "reason": "Timings inquiry."},
    {"text": "मी सुरक्षित आहे, फक्त शिष्यवृत्ती अर्जाबद्दल माहिती हवी आहे.", "language": "Marathi", "risk_level": "LOW", "reason": "Safe statement with scholarship query."},
    {"text": "दाखल्यामध्ये जन्मतारीख दुरुस्त करण्याची पद्धत सांगावी.", "language": "Marathi", "risk_level": "LOW", "reason": "Date correction procedural request."},
    {"text": "ऑनलाइन पोर्टलवर अर्ज कसा सादर करावा याबद्दल मार्गदर्शन हवे.", "language": "Marathi", "risk_level": "LOW", "reason": "Portal submission guidance."},
    {"text": "माझी वीज बिलाची पावती पोर्टलवर दिसत नाहीये.", "language": "Marathi", "risk_level": "LOW", "reason": "Receipt visibility check."},
    {"text": "ग्रामपंचायत कार्यालयाचा ईमेल पत्ता काय आहे?", "language": "Marathi", "risk_level": "LOW", "reason": "Email address inquiry."},
    {"text": "वृद्धापकाळ निवृत्तीवेतन योजनेचे नियम काय आहेत?", "language": "Marathi", "risk_level": "LOW", "reason": "Pension scheme rule inquiry."},

    # Romanized Marathi LOW
    {"text": "Majhya takraricha status kasa check karava te sanga please.", "language": "Romanized Marathi", "risk_level": "LOW", "reason": "Status check guidance in Romanized Marathi."},
    {"text": "Mala ration card sathi form kuthe bhetel?", "language": "Romanized Marathi", "risk_level": "LOW", "reason": "Form availability inquiry."},
    {"text": "Documents submit kele hote, verification complete zale ka?", "language": "Romanized Marathi", "risk_level": "LOW", "reason": "Submission verification status."},
    {"text": "Office chi timing kay ahe ani Saturday chalu asate ka?", "language": "Romanized Marathi", "risk_level": "LOW", "reason": "Working hours check."},
    {"text": "Mala reference number SMS var ala nahi ajun.", "language": "Romanized Marathi", "risk_level": "LOW", "reason": "SMS tracking confirmation."},
    {"text": "Mi safe ahe, fakt pension badal thodi mahiti havi hoti.", "language": "Romanized Marathi", "risk_level": "LOW", "reason": "Safe affirmation with pension query."},
    {"text": "Electricity bill re-check karnyasathi application kashi karaychi?", "language": "Romanized Marathi", "risk_level": "LOW", "reason": "Application filing inquiry."},
    {"text": "Online account password reset karnya sathi help pahije.", "language": "Romanized Marathi", "risk_level": "LOW", "reason": "Password reset inquiry."},
    {"text": "Ward officer cha phone number share kara please.", "language": "Romanized Marathi", "risk_level": "LOW", "reason": "Ward officer contact request."},
    {"text": "Scholarship list kadhi declare honar ahe?", "language": "Romanized Marathi", "risk_level": "LOW", "reason": "Scholarship announcement date."},
    {"text": "Birth certificate download karnyachi link dya.", "language": "Romanized Marathi", "risk_level": "LOW", "reason": "Download link request."},

    # Mixed LOW
    {"text": "Hello, mujhe application status check karna hai, please help me with the portal link.", "language": "Mixed", "risk_level": "LOW", "reason": "Polite mixed bilingual status check."},
    {"text": "I submitted the form online, pan acknowledgment receipt download hot nahiye.", "language": "Mixed", "risk_level": "LOW", "reason": "Mixed technical issue report."},
    {"text": "Complaint registration zala ahe, what is the next step in the procedure?", "language": "Mixed", "risk_level": "LOW", "reason": "Procedure next-step query."},
    {"text": "Sir, document list bhej dijiye so that I can submit it tomorrow morning.", "language": "Mixed", "risk_level": "LOW", "reason": "Document checklist request."},
    {"text": "I am feeling quite okay, just wanted to verify if my address change request is approved.", "language": "Mixed", "risk_level": "LOW", "reason": "Safe expression with address verification."},
    {"text": "Please provide the email ID of the grievance officer, mujhe ek enquiry bhejni hai.", "language": "Mixed", "risk_level": "LOW", "reason": "Email address inquiry."},
    {"text": "Water pipeline work kadhi complete honar, any estimated date?", "language": "Mixed", "risk_level": "LOW", "reason": "Public work completion date query."},
    {"text": "I checked the portal today, status pending dikha raha hai.", "language": "Mixed", "risk_level": "LOW", "reason": "Routine portal status inquiry."},
    {"text": "Mera pension case transfer hua hai, which office should I visit now?", "language": "Mixed", "risk_level": "LOW", "reason": "Office jurisdiction inquiry."},
    {"text": "Can I submit the affidavit in Marathi or English format?", "language": "Mixed", "risk_level": "LOW", "reason": "Document language acceptance inquiry."},
    {"text": "Helpline number var call lagat nahiye, is there any alternate number?", "language": "Mixed", "risk_level": "LOW", "reason": "Alternate telephone inquiry."},

    # =========================================================================
    # MODERATE RISK (~66 examples): Sustained stress, feeling overwhelmed, confusion, coping trouble, fatigue
    # =========================================================================
    # English MODERATE
    {"text": "I’ve been feeling overwhelmed for the past few days and I don’t know how to deal with this situation.", "language": "English", "risk_level": "MODERATE", "reason": "Sustained emotional fatigue and coping difficulty."},
    {"text": "I am getting very stressed because my pension has not arrived and expenses are piling up.", "language": "English", "risk_level": "MODERATE", "reason": "Financial strain causing noticeable stress."},
    {"text": "Everything feels confusing and exhausting, I don't know who to turn to for guidance.", "language": "English", "risk_level": "MODERATE", "reason": "Mental fatigue and lack of direction."},
    {"text": "I have been visiting the office repeatedly for three months, it is extremely draining.", "language": "English", "risk_level": "MODERATE", "reason": "Bureaucratic frustration and emotional exhaustion."},
    {"text": "The continuous uncertainty regarding my job application is making me anxious and sleepless.", "language": "English", "risk_level": "MODERATE", "reason": "Situational anxiety with mild sleep disturbance."},
    {"text": "I am having difficulty managing the paperwork on my own and feel burdened by it.", "language": "English", "risk_level": "MODERATE", "reason": "Cognitive burden and operational overload."},
    {"text": "No one is answering my calls and I am starting to feel restless and distressed.", "language": "English", "risk_level": "MODERATE", "reason": "Communication breakdown leading to distress."},
    {"text": "It feels like nothing is moving forward and the pressure is building up every day.", "language": "English", "risk_level": "MODERATE", "reason": "Cumulative pressure without immediate crisis."},
    {"text": "I need some supportive advice because I am having trouble coping with all these delays.", "language": "English", "risk_level": "MODERATE", "reason": "Help-seeking for emotional coping."},
    {"text": "My family is constantly arguing over this land dispute and the mental strain is heavy.", "language": "English", "risk_level": "MODERATE", "reason": "Interpersonal strain causing psychological stress."},
    {"text": "I am really struggling to understand what they want from me in this legal notice.", "language": "English", "risk_level": "MODERATE", "reason": "Procedural confusion accompanied by distress."},

    # Hindi MODERATE
    {"text": "मुझे काफी स्ट्रेस हो रहा है और मुझे समझ नहीं आ रहा कि मैं क्या करूँ।", "language": "Hindi", "risk_level": "MODERATE", "reason": "Expressed stress and feeling lost."},
    {"text": "पिछले कई हफ़्तों से लगातार चक्कर काट रहा हूँ, बहुत ज्यादा मानसिक थकान हो गई है।", "language": "Hindi", "risk_level": "MODERATE", "reason": "Persistent frustration and mental fatigue."},
    {"text": "पेंशन न मिलने की वजह से घर का खर्च चलाना बहुत मुश्किल हो गया है, बहुत तनाव है।", "language": "Hindi", "risk_level": "MODERATE", "reason": "Financial hardship with substantial stress."},
    {"text": "सब कुछ बहुत उलझा हुआ लग रहा है और मुझे कोई रास्ता दिखाई नहीं दे रहा।", "language": "Hindi", "risk_level": "MODERATE", "reason": "Cognitive confusion and feeling overwhelmed."},
    {"text": "अधिकारी ठीक से बात नहीं कर रहे हैं, जिससे मेरी चिंता बढ़ती ही जा रही है।", "language": "Hindi", "risk_level": "MODERATE", "reason": "Increasing anxiety due to unhelpful staff."},
    {"text": "इस परेशानी की वजह से मुझे रात को ठीक से नींद भी नहीं आ रही है।", "language": "Hindi", "risk_level": "MODERATE", "reason": "Distress affecting sleep patterns."},
    {"text": "मुझ पर इस काम को पूरा करने का बहुत भारी दबाव है और मैं अकेला पड़ गया हूँ।", "language": "Hindi", "risk_level": "MODERATE", "reason": "Pressure and feeling unsupported."},
    {"text": "मुझे थोड़ी मानसिक सहायता और सही सलाह की सख्त जरूरत महसूस हो रही है।", "language": "Hindi", "risk_level": "MODERATE", "reason": "Seeking emotional and procedural support."},
    {"text": "दवाइयों के पैसे खत्म हो रहे हैं और सरकारी सहायता अभी तक नहीं मिली, बहुत घबराहट है।", "language": "Hindi", "risk_level": "MODERATE", "reason": "Health-related financial vulnerability."},
    {"text": "मैं बहुत परेशान हूँ, कृपया मुझे बताइए कि मैं इस समस्या को कैसे सुलझाऊँ।", "language": "Hindi", "risk_level": "MODERATE", "reason": "General distress and help request."},
    {"text": "कागजी कार्रवाई इतनी कठिन है कि मैं इसे संभाल नहीं पा रहा हूँ।", "language": "Hindi", "risk_level": "MODERATE", "reason": "Inability to handle bureaucratic burden."},

    # Hinglish MODERATE
    {"text": "Mujhe kaafi stress ho raha hai aur samajh nahi aa raha kaise handle karun.", "language": "Hinglish", "risk_level": "MODERATE", "reason": "Coping difficulty and expressed stress in Hinglish."},
    {"text": "Pichle ek mahine se har roz tension me hoon, koi proper response nahi de raha.", "language": "Hinglish", "risk_level": "MODERATE", "reason": "Persistent daily tension due to lack of response."},
    {"text": "Is issue ki wajah se mera mental peace disturb ho gaya hai completely.", "language": "Hinglish", "risk_level": "MODERATE", "reason": "Loss of mental peace from prolonged dispute."},
    {"text": "Salary hold par hai aur family expenses manage karna impossible lag raha hai.", "language": "Hinglish", "risk_level": "MODERATE", "reason": "Financial strain and anxiety."},
    {"text": "Mujhe bahut overwhelming lag raha hai, itne saare notices samajh nahi aa rahe.", "language": "Hinglish", "risk_level": "MODERATE", "reason": "Notice overload and cognitive exhaustion."},
    {"text": "Roz office ke chakkar kaat kar main thak chuka hoon mental level par.", "language": "Hinglish", "risk_level": "MODERATE", "reason": "Mental exhaustion from repeated visits."},
    {"text": "Kuch samajh nahi aa raha kisse baat karun, bahut confusion aur pressure hai.", "language": "Hinglish", "risk_level": "MODERATE", "reason": "Confusion and situational pressure."},
    {"text": "Medical bills pending hain aur insurance claim delay ho raha hai, bahut anxiety hai.", "language": "Hinglish", "risk_level": "MODERATE", "reason": "Healthcare billing anxiety."},
    {"text": "Mujhe kisi understanding counselor ya officer se baat karni hai guidance ke liye.", "language": "Hinglish", "risk_level": "MODERATE", "reason": "Request for counseling/guidance."},
    {"text": "Dheere dheere situation mere control se bahar ja rahi hai aisa feel hota hai.", "language": "Hinglish", "risk_level": "MODERATE", "reason": "Perceived loss of control."},
    {"text": "Itna mental pressure pehle kabhi feel nahi kiya, guidance chahiye.", "language": "Hinglish", "risk_level": "MODERATE", "reason": "High perceived pressure requiring advice."},

    # Marathi MODERATE
    {"text": "मला खूप ताण येत आहे आणि मला कोणाशी तरी बोलायचे आहे. कृपया मदत करा.", "language": "Marathi", "risk_level": "MODERATE", "reason": "Expressed stress and need for conversation in Marathi."},
    {"text": "गेल्या काही दिवसांपासून खूप मानसिक त्रास सहन करावा लागत आहे.", "language": "Marathi", "risk_level": "MODERATE", "reason": "Sustained mental suffering over days."},
    {"text": "वारंवार चकरा मारूनही काम होत नसल्याने मी खूप निराश झालो आहे.", "language": "Marathi", "risk_level": "MODERATE", "reason": "Despair from unfulfilled administrative visits."},
    {"text": "घरखर्च कसा चालवायचा या विवंचनेमुळे रात्रीची झोप उडाली आहे.", "language": "Marathi", "risk_level": "MODERATE", "reason": "Financial anxiety affecting sleep."},
    {"text": "या समस्येचा भार माझ्यावर खूप जास्त होत चालला आहे.", "language": "Marathi", "risk_level": "MODERATE", "reason": "Heavy emotional burden."},
    {"text": "मला योग्य मार्गदर्शन हवे आहे कारण परिस्थिती हाताबाहेर जात असल्याचे वाटते.", "language": "Marathi", "risk_level": "MODERATE", "reason": "Guidance request to regain control."},
    {"text": "कार्यालयात कोणीही व्यवस्थित उत्तर देत नाही, यामुळे माझी काळजी वाढली आहे.", "language": "Marathi", "risk_level": "MODERATE", "reason": "Staff indifference increasing worry."},
    {"text": "कागदपत्रांची पूर्तता करताना मला प्रचंड गोंधळ आणि ताण जाणवत आहे.", "language": "Marathi", "risk_level": "MODERATE", "reason": "Confusion and stress during documentation."},
    {"text": "आईच्या आजारपणाचा खर्च आणि या पेन्शनचा खोळंबा यामुळे मी पुरता खचलो आहे.", "language": "Marathi", "risk_level": "MODERATE", "reason": "Caregiver burden combined with pension delay."},
    {"text": "मला थोड्या मानसिक आधाराची आणि समुपदेशनाची गरज आहे.", "language": "Marathi", "risk_level": "MODERATE", "reason": "Explicit request for psychological/counseling support."},
    {"text": "या सततच्या चिंतेमुळे दैनंदिन कामावर लक्ष केंद्रित करणे कठीण झाले आहे.", "language": "Marathi", "risk_level": "MODERATE", "reason": "Impaired concentration from persistent anxiety."},

    # Romanized Marathi MODERATE
    {"text": "Mala support pahije please mala khup tension yetoy ani kay karu samjat nahiye.", "language": "Romanized Marathi", "risk_level": "MODERATE", "reason": "Tension and confusion in Romanized Marathi."},
    {"text": "Khup mental stress ahe office chya chakkar marun, thaklo ahe mi.", "language": "Romanized Marathi", "risk_level": "MODERATE", "reason": "Mental exhaustion from repeated visits."},
    {"text": "Situation khup overwhelming ahe ani family madhe pan khup bhandan hot ahet.", "language": "Romanized Marathi", "risk_level": "MODERATE", "reason": "Domestic conflict amplifying stress."},
    {"text": "Paisa cha problem ahe ani ration card issue solve hot nahi, khup worry hotiye.", "language": "Romanized Marathi", "risk_level": "MODERATE", "reason": "Poverty-related strain and anxiety."},
    {"text": "Mala konatri samjun ghenara manus hava ahe guidance sathi.", "language": "Romanized Marathi", "risk_level": "MODERATE", "reason": "Need for an empathetic advisor."},
    {"text": "Sarv kahi complicated zala ahe, kay step ghyavi kalat nahiye.", "language": "Romanized Marathi", "risk_level": "MODERATE", "reason": "Procedural confusion causing stagnation."},
    {"text": "Ratri zop yet nahi ya tension mule, khoop pressure vat-tay.", "language": "Romanized Marathi", "risk_level": "MODERATE", "reason": "Insomnia from situation-related pressure."},
    {"text": "Maja aayushyat khup motha problem suru ahe, please thodi madat kara.", "language": "Romanized Marathi", "risk_level": "MODERATE", "reason": "Perceived major life problem requesting help."},
    {"text": "Documents samajnyat adchan yete ahe ani officers help karat nahit.", "language": "Romanized Marathi", "risk_level": "MODERATE", "reason": "Lack of institutional support causing distress."},
    {"text": "Manavar khup vajan vat-tay, kase baher padu ya madhun?", "language": "Romanized Marathi", "risk_level": "MODERATE", "reason": "Heavy emotional burden seeking way out."},
    {"text": "Continuous delays mule confidence kami hot चालला ahe.", "language": "Romanized Marathi", "risk_level": "MODERATE", "reason": "Eroding confidence due to bureaucratic delays."},

    # Mixed MODERATE
    {"text": "I am feeling worried mujhe process ke baare mein information chahiye, bohot tension ho rahi hai.", "language": "Mixed", "risk_level": "MODERATE", "reason": "Mixed complaint with both inquiry and tension."},
    {"text": "I feel so overwhelmed by these official notices, samajh nahi aa raha kaise reply karun.", "language": "Mixed", "risk_level": "MODERATE", "reason": "Notice overwhelm and difficulty responding."},
    {"text": "No one is helping me at the center, mala khup tension yet ahe please guide.", "language": "Mixed", "risk_level": "MODERATE", "reason": "Lack of help creating noticeable distress."},
    {"text": "My health is suffering due to this prolonged case, bahut zyada mental strain hai.", "language": "Mixed", "risk_level": "MODERATE", "reason": "Physical health impact from prolonged dispute."},
    {"text": "It has been six months without income, ghar kaise chalega iski bohot chinta hai.", "language": "Mixed", "risk_level": "MODERATE", "reason": "Severe livelihood worry."},
    {"text": "I am unable to handle this alone, mala thoda counseling support pahije.", "language": "Mixed", "risk_level": "MODERATE", "reason": "Inability to cope alone requesting counseling."},
    {"text": "Every officer gives different rules, bahut frustration aur anxiety hoti hai.", "language": "Mixed", "risk_level": "MODERATE", "reason": "Conflicting guidance driving anxiety."},
    {"text": "I am completely exhausted trying to resolve this, kharach khup tras hoto ahe.", "language": "Mixed", "risk_level": "MODERATE", "reason": "Exhaustion and suffering from unresolved issue."},
    {"text": "Please connect me to someone who can listen, situation bahut stressful ho gayi hai.", "language": "Mixed", "risk_level": "MODERATE", "reason": "Seeking empathetic listener."},
    {"text": "The continuous rejection of my appeal is breaking my confidence, khup dukh hotay.", "language": "Mixed", "risk_level": "MODERATE", "reason": "Repeated rejection leading to despair."},
    {"text": "I am trying my best to manage, lekin pressure din ba din badhta ja raha hai.", "language": "Mixed", "risk_level": "MODERATE", "reason": "Escalating situational pressure."},

    # =========================================================================
    # HIGH RISK (~66 examples): Extreme fear, intense vulnerability, severe distress, breakdown, isolation, feeling helpless
    # =========================================================================
    # English HIGH
    {"text": "I am feeling extreme fear and pressure. I have no one to support me and I cannot cope with this.", "language": "English", "risk_level": "HIGH", "reason": "Extreme fear, isolation, and coping failure."},
    {"text": "I am completely terrified of what will happen to my children if we lose our shelter.", "language": "English", "risk_level": "HIGH", "reason": "Terrifying existential vulnerability regarding shelter and family."},
    {"text": "I feel so helpless and abandoned, there is nobody left to help me in this dark time.", "language": "English", "risk_level": "HIGH", "reason": "Severe abandonment and helplessness."},
    {"text": "The pressure is unbearable, I am having panic attacks and I don't know what to do.", "language": "English", "risk_level": "HIGH", "reason": "Unbearable pressure with physiological panic attacks."},
    {"text": "They have cut off our water and electricity, my sick mother has no medicines and I am desperate.", "language": "English", "risk_level": "HIGH", "reason": "Severe humanitarian vulnerability and desperation."},
    {"text": "I am trembling with anxiety, I feel completely trapped and cornered by these threats.", "language": "English", "risk_level": "HIGH", "reason": "Trembling anxiety and feeling cornered."},
    {"text": "I have lost everything in this fraud and I feel totally broken inside with no hope.", "language": "English", "risk_level": "HIGH", "reason": "Severe loss and perceived hopelessness."},
    {"text": "I am alone in a strange city with no money and no place to stay tonight, please help.", "language": "English", "risk_level": "HIGH", "reason": "Immediate homelessness and acute vulnerability."},
    {"text": "The mental agony is too much for me to endure any longer, I desperately need someone to intervene.", "language": "English", "risk_level": "HIGH", "reason": "High emotional agony seeking immediate intervention."},
    {"text": "I feel so unsafe because people are constantly stalking outside my door at night.", "language": "English", "risk_level": "HIGH", "reason": "High safety fear from persistent stalking."},
    {"text": "I am having severe breakdowns daily and cannot look after my basic needs anymore.", "language": "English", "risk_level": "HIGH", "reason": "Functional impairment and daily breakdowns."},

    # Hindi HIGH
    {"text": "मुझे बहुत ज्यादा डर लग रहा है और ऐसा लगता है कि मैं पूरी तरह टूट चुका हूँ।", "language": "Hindi", "risk_level": "HIGH", "reason": "Intense fear and feeling completely shattered."},
    {"text": "मेरे पास कोई सहारा नहीं बचा है, मैं बिल्कुल अकेला और असहाय महसूस कर रहा हूँ।", "language": "Hindi", "risk_level": "HIGH", "reason": "Extreme isolation, lack of support, and helplessness."},
    {"text": "धमकियों की वजह से मेरा पूरा परिवार दहशत में जी रहा है, हमें बहुत खतरा महसूस हो रहा है।", "language": "Hindi", "risk_level": "HIGH", "reason": "Family living in terror due to threats."},
    {"text": "मुझे लगातार पैनिक अटैक आ रहे हैं और मैं इस असहनीय दर्द को झेल नहीं पा रहा हूँ।", "language": "Hindi", "risk_level": "HIGH", "reason": "Severe panic attacks and unbearable agony."},
    {"text": "हमारे पास खाने के लिए कुछ नहीं बचा है और बच्चे भूख से रो रहे हैं, कोई हमारी मदद करे।", "language": "Hindi", "risk_level": "HIGH", "reason": "Acute humanitarian crisis with starving children."},
    {"text": "मेरी हालत बहुत खराब है, मुझे तुरंत किसी वरिष्ठ अधिकारी की सहायता चाहिए।", "language": "Hindi", "risk_level": "HIGH", "reason": "Deteriorating state requesting urgent senior intervention."},
    {"text": "दबंग लोग मेरी ज़मीन छीनने की कोशिश कर रहे हैं और मुझे जान का डर सता रहा है।", "language": "Hindi", "risk_level": "HIGH", "reason": "Land grabbing accompanied by fear for life."},
    {"text": "मैं डिप्रेशन की गहराइयों में डूब रहा हूँ और खुद को संभालना नामुमकिन लग रहा है।", "language": "Hindi", "risk_level": "HIGH", "reason": "Severe emotional distress and inability to self-regulate."},
    {"text": "मुझे लगता है कि अगर किसी ने मदद नहीं की तो सब कुछ हमेशा के लिए बर्बाद हो जाएगा।", "language": "Hindi", "risk_level": "HIGH", "reason": "Impending catastrophe and acute distress."},
    {"text": "मैं बहुत कांप रहा हूँ और बोलने की हालत में भी नहीं हूँ, कृपया तुरंत सुनिए।", "language": "Hindi", "risk_level": "HIGH", "reason": "Physical trembling and acute distress."},
    {"text": "मेरे साथ बहुत बड़ा अन्याय हुआ है और मेरा जीवन संकट में पड़ गया है।", "language": "Hindi", "risk_level": "HIGH", "reason": "Injustice combined with perceived life crisis."},

    # Hinglish HIGH
    {"text": "Mujhe bahut fear aur pressure feel ho raha hai. Lagta hai main bacha nahi paunga sab kuch.", "language": "Hinglish", "risk_level": "HIGH", "reason": "Extreme fear and feeling unable to save situation."},
    {"text": "Main completely helpless feel kar raha hoon, koi bhi support system nahi bacha.", "language": "Hinglish", "risk_level": "HIGH", "reason": "Total helplessness and absence of support."},
    {"text": "Mujhe panic attacks aa rahe hain aur heart beat bohot tez ho rahi hai darr se.", "language": "Hinglish", "risk_level": "HIGH", "reason": "Severe physiological anxiety and panic."},
    {"text": "Local goons daily threaten kar rahe hain, mujhe bohot khatra mehsoos ho raha hai.", "language": "Hinglish", "risk_level": "HIGH", "reason": "Daily threats from local elements causing severe fear."},
    {"text": "Mera sab kuch chheen liya gaya hai, main sadak par aa gaya hoon bina kisi sahare ke.", "language": "Hinglish", "risk_level": "HIGH", "reason": "Severe destitution and abandonment."},
    {"text": "Mental pressure itna extreme ho chuka hai ki I cannot think clearly at all.", "language": "Hinglish", "risk_level": "HIGH", "reason": "Cognitive paralysis from extreme pressure."},
    {"text": "Mujhe urgent protection chahiye, mere ghar ke bahar suspicious log ghoom rahe hain.", "language": "Hinglish", "risk_level": "HIGH", "reason": "Suspicious persons outside home requiring protection."},
    {"text": "Main itna toot chuka hoon ki bed se uthne ki bhi himmat nahi bachi.", "language": "Hinglish", "risk_level": "HIGH", "reason": "Severe emotional breakdown and avolition."},
    {"text": "Please send someone immediately, my landlord is forcefully throwing my luggage out.", "language": "Hinglish", "risk_level": "HIGH", "reason": "Forcible eviction in progress."},
    {"text": "Mujhe lagta hai mere saath bohot bada dhokha hua hai aur ab koi umeed nahi hai.", "language": "Hinglish", "risk_level": "HIGH", "reason": "Deep despair and hopelessness following fraud."},
    {"text": "Main bilkul akela pad gaya hoon is musibat me, please help me urgently.", "language": "Hinglish", "risk_level": "HIGH", "reason": "Extreme isolation during urgent crisis."},

    # Marathi HIGH
    {"text": "मला खूप भीती वाटते आहे आणि मला कोणीही आधार देणारे नाही. मी पूर्णपणे हताश झालो आहे.", "language": "Marathi", "risk_level": "HIGH", "reason": "Intense fear, lack of support, and profound despair in Marathi."},
    {"text": "माझ्यावर प्रचंड दबाव आहे आणि मला सहन होत नाहीये, मला तातडीने मदतीची गरज आहे.", "language": "Marathi", "risk_level": "HIGH", "reason": "Unbearable pressure demanding urgent help."},
    {"text": "गुंडांकडून मला धमक्या येत आहेत आणि मी घरातून बाहेर पडायलाही घाबरत आहे.", "language": "Marathi", "risk_level": "HIGH", "reason": "Fear of leaving home due to criminal threats."},
    {"text": "माझे कुटुंब रस्त्यावर येण्याची वेळ आली आहे, आम्ही पूर्णपणे असहाय्य झालो आहोत.", "language": "Marathi", "risk_level": "HIGH", "reason": "Family facing impending homelessness and helplessness."},
    {"text": "मी इतका खचलो आहे की आता पुढे काय करावे हे सुचत नाही, भयानक भीती वाटते.", "language": "Marathi", "risk_level": "HIGH", "reason": "Extreme demoralization and terror."},
    {"text": "माझ्या आजारी मुलाला औषध नाही आणि पैसे संपले आहेत, कृपया तातडीने हस्तक्षेप करा.", "language": "Marathi", "risk_level": "HIGH", "reason": "Critical child medical emergency and poverty."},
    {"text": "मला सतत भीती वाटते की काहीतरी खूप वाईट घडणार आहे.", "language": "Marathi", "risk_level": "HIGH", "reason": "Persistent dread of impending catastrophe."},
    {"text": "कार्यालयात मला अपमानास्पद वागणूक दिली गेली आणि मला एकाकी पाडले गेले.", "language": "Marathi", "risk_level": "HIGH", "reason": "Humiliation, harassment, and severe isolation."},
    {"text": "माझी मानसिक स्थिती अत्यंत नाजूक झाली आहे, मला कोणाची तरी त्वरित साथ हवी आहे.", "language": "Marathi", "risk_level": "HIGH", "reason": "Fragile psychological state needing immediate companion."},
    {"text": "घर खाली करण्याची नोटीस आली आहे आणि आमच्याकडे जाण्यासाठी दुसरी कोणतीही जागा नाही.", "language": "Marathi", "risk_level": "HIGH", "reason": "Eviction with zero shelter alternatives."},
    {"text": "मी प्रचंड दहशतीखाली जगत आहे, मला संरक्षण हवे आहे.", "language": "Marathi", "risk_level": "HIGH", "reason": "Living under severe terror, requesting protection."},

    # Romanized Marathi HIGH
    {"text": "Mala bhiti vatat ahe khoop ani konich nahiye madatila, mi purna asahay zhalo ahe.", "language": "Romanized Marathi", "risk_level": "HIGH", "reason": "Intense fear and complete helplessness in Romanized Marathi."},
    {"text": "Gharatle lok khup tras det ahet ani mala kiti divas he sahan karava lagel kalat nahi.", "language": "Romanized Marathi", "risk_level": "HIGH", "reason": "Severe domestic harassment."},
    {"text": "Dhamkya yet ahet phone var, mi khup ghabarlo ahe please protection dya.", "language": "Romanized Marathi", "risk_level": "HIGH", "reason": "Phone threats and terror demanding protection."},
    {"text": "Maja aayushya purna udhvast zale ahe ya fraud mule, mi ekta padlo ahe.", "language": "Romanized Marathi", "risk_level": "HIGH", "reason": "Devastation and isolation following scam."},
    {"text": "Aamchyakade khayala anna pan nahiye, urgent madat pahije aamhala.", "language": "Romanized Marathi", "risk_level": "HIGH", "reason": "Severe food insecurity."},
    {"text": "Manat khup bhiti basli ahe, ratri thartharat uthto mi.", "language": "Romanized Marathi", "risk_level": "HIGH", "reason": "Physical trembling and night terrors."},
    {"text": "Gund lok ghar samor yeun shivigol karat ahet, khup danger vat-tay.", "language": "Romanized Marathi", "risk_level": "HIGH", "reason": "Aggressive confrontation in front of home."},
    {"text": "Mi emotionally purna breakdown zhalo ahe, please someone talk to me.", "language": "Romanized Marathi", "risk_level": "HIGH", "reason": "Severe emotional breakdown pleading for human contact."},
    {"text": "Paisa nahi, ghari aajarpan ahe, mi control haravun baslo ahe.", "language": "Romanized Marathi", "risk_level": "HIGH", "reason": "Poverty, illness, and total loss of control."},
    {"text": "Koni tari mothe sankat aalay amchya var, rescue support hava ahe.", "language": "Romanized Marathi", "risk_level": "HIGH", "reason": "Major crisis requiring rescue support."},
    {"text": "Police complaint karayla pan ghabarto ahe mi tyanche lok tithe ahet.", "language": "Romanized Marathi", "risk_level": "HIGH", "reason": "Fear of institutional retaliation."},

    # Mixed HIGH
    {"text": "I am feeling extreme fear and pressure, mujhe lagta hai koi meri sun nahi raha.", "language": "Mixed", "risk_level": "HIGH", "reason": "Severe fear and feeling completely unheard."},
    {"text": "People are threatening my family, mala khup bhiti vatat ahe please send police help.", "language": "Mixed", "risk_level": "HIGH", "reason": "Family threats demanding police intervention."},
    {"text": "I am having severe anxiety attacks, haath kaamp rahe hain aur main breathe nahi kar pa raha.", "language": "Mixed", "risk_level": "HIGH", "reason": "Severe panic attack with hyperventilation."},
    {"text": "Everything is collapsing around me, koi sahara nahi hai, totally alone in this city.", "language": "Mixed", "risk_level": "HIGH", "reason": "Catastrophic collapse and urban isolation."},
    {"text": "My husband took all money and locked me out, mala urgently shelter home madat pahije.", "language": "Mixed", "risk_level": "HIGH", "reason": "Domestic lockout and urgent shelter need."},
    {"text": "They are harassing me constantly, main itna terrorize ho chuka hoon ki bahar nahi nikal sakta.", "language": "Mixed", "risk_level": "HIGH", "reason": "Severe harassment and confinement from terror."},
    {"text": "I feel completely cornered and desperate, kharach maja dhairya sampat aalay.", "language": "Mixed", "risk_level": "HIGH", "reason": "Cornered desperation and exhaustion of endurance."},
    {"text": "Medical emergency hai ghar me aur paise zero hain, please assist urgently.", "language": "Mixed", "risk_level": "HIGH", "reason": "Acute medical emergency with zero financial resources."},
    {"text": "I cannot take this torment anymore, I am having uncontrollable crying spells daily.", "language": "Mixed", "risk_level": "HIGH", "reason": "Severe emotional dysregulation and distress."},
    {"text": "The goons told me they will harm my shop today, mujhe security support chahiye.", "language": "Mixed", "risk_level": "HIGH", "reason": "Imminent threat to business premises."},
    {"text": "I am abandoned with a newborn baby, khup mothe sankat ahe please provide help.", "language": "Mixed", "risk_level": "HIGH", "reason": "Maternal abandonment with infant in acute distress."},

    # =========================================================================
    # CRITICAL RISK (~66 examples): Explicit or implicit safety concerns, inability to stay safe, acute crisis, life in danger, emergency
    # =========================================================================
    # English CRITICAL
    {"text": "I do not feel safe right now. I need immediate help. I cannot stay safe and I am alone.", "language": "English", "risk_level": "CRITICAL", "reason": "Acute personal safety danger and isolation."},
    {"text": "I don't feel safe in this house and I am terrified that someone will hurt me tonight.", "language": "English", "risk_level": "CRITICAL", "reason": "Imminent domestic physical danger."},
    {"text": "I’m worried that I may not be able to keep myself safe under this intense pressure.", "language": "English", "risk_level": "CRITICAL", "reason": "Inability to maintain personal safety under pressure."},
    {"text": "Please dispatch emergency assistance immediately, someone is actively breaking into my home.", "language": "English", "risk_level": "CRITICAL", "reason": "Active home invasion in progress."},
    {"text": "I cannot guarantee my safety right now, I desperately need immediate protection.", "language": "English", "risk_level": "CRITICAL", "reason": "Inability to guarantee personal safety."},
    {"text": "They have threatened to kill me if I step outside, I am trapped and in grave danger.", "language": "English", "risk_level": "CRITICAL", "reason": "Direct death threat with physical confinement."},
    {"text": "I am in an acute physical emergency, I am bleeding and need urgent medical rescue.", "language": "English", "risk_level": "CRITICAL", "reason": "Acute physical trauma requiring urgent rescue."},
    {"text": "I do not feel safe at all, please connect me to the crisis operator right now.", "language": "English", "risk_level": "CRITICAL", "reason": "Crisis safety escalation request."},
    {"text": "My partner has become violent and I am locked in the bathroom with my baby.", "language": "English", "risk_level": "CRITICAL", "reason": "Acute domestic violence situation."},
    {"text": "I am in imminent danger, please help me right away before it is too late.", "language": "English", "risk_level": "CRITICAL", "reason": "Imminent life-threatening danger."},
    {"text": "I cannot stay safe in this environment, my life is under immediate threat.", "language": "English", "risk_level": "CRITICAL", "reason": "Immediate life threat in unsafe environment."},

    # Hindi CRITICAL
    {"text": "मुझे अभी बिल्कुल सुरक्षित महसूस नहीं हो रहा है, मुझे तुरंत सहायता चाहिए।", "language": "Hindi", "risk_level": "CRITICAL", "reason": "Acute feeling of being unsafe requiring immediate help in Hindi."},
    {"text": "मुझे डर है कि मैं खुद को सुरक्षित नहीं रख पाऊँगा, कृपया तुरंत कोई कदम उठाएं।", "language": "Hindi", "risk_level": "CRITICAL", "reason": "Inability to keep self safe."},
    {"text": "मेरी जान को बहुत बड़ा खतरा है, कुछ लोग हथियार लेकर मेरे घर के बाहर खड़े हैं।", "language": "Hindi", "risk_level": "CRITICAL", "reason": "Armed threat outside home targeting life."},
    {"text": "मुझे तुरंत सुरक्षा चाहिए, मुझ पर शारीरिक हमला हुआ है और मैं घायल हूँ।", "language": "Hindi", "risk_level": "CRITICAL", "reason": "Physical assault with injury requiring immediate protection."},
    {"text": "मैं अपनी सुरक्षा नहीं कर पा रहा हूँ, मेरी जान बचा लीजिए।", "language": "Hindi", "risk_level": "CRITICAL", "reason": "Plea for life rescue due to inability to stay safe."},
    {"text": "मुझे जान से मारने की धमकी दी गई है, मैं कमरे में बंद हूँ और बहुत डरा हुआ हूँ।", "language": "Hindi", "risk_level": "CRITICAL", "reason": "Death threat with confinement."},
    {"text": "यहाँ बहुत बड़ा संकट है, तुरंत पुलिस या इमरजेंसी टीम को भेजिए।", "language": "Hindi", "risk_level": "CRITICAL", "reason": "Major emergency requesting immediate dispatch."},
    {"text": "मैं सुरक्षित नहीं हूँ और मुझे नहीं पता कि अगले पल मेरे साथ क्या होगा।", "language": "Hindi", "risk_level": "CRITICAL", "reason": "Critical uncertainty about immediate physical safety."},
    {"text": "मेरे साथ घरेलू हिंसा हो रही है और मुझे अपनी जान का खतरा लग रहा है।", "language": "Hindi", "risk_level": "CRITICAL", "reason": "Acute domestic violence endangering life."},
    {"text": "कृपया तुरंत ऑपरेटर से बात कराइए, यह जिंदगी और मौत का सवाल है।", "language": "Hindi", "risk_level": "CRITICAL", "reason": "Matter of life and death demanding immediate operator."},
    {"text": "मेरी स्थिति अत्यंत गंभीर है, मैं खुद को सुरक्षित रखने में असमर्थ हूँ।", "language": "Hindi", "risk_level": "CRITICAL", "reason": "Critical inability to maintain safety."},

    # Hinglish CRITICAL
    {"text": "Mujhe abhi safe feel nahi ho raha. Mujhe immediate help chahiye, main akela hoon.", "language": "Hinglish", "risk_level": "CRITICAL", "reason": "Direct unsafe declaration and immediate need in Hinglish."},
    {"text": "Mujhe chinta hai ki main khud ko safe nahi rakh paunga, please intervene.", "language": "Hinglish", "risk_level": "CRITICAL", "reason": "Apprehension about personal safety."},
    {"text": "Meri life danger me hai right now, kisi ne mere darwaze par petrol daal diya hai.", "language": "Hinglish", "risk_level": "CRITICAL", "reason": "Imminent arson and life threat."},
    {"text": "Mujhe physical assault kiya gaya hai aur mujhe emergency police help chahiye.", "language": "Hinglish", "risk_level": "CRITICAL", "reason": "Physical violence requiring emergency police."},
    {"text": "Main bilkul safe nahi hoon, wo log mujhe dhoond rahe hain marne ke liye.", "language": "Hinglish", "risk_level": "CRITICAL", "reason": "Actively hunted with murderous intent."},
    {"text": "I am in danger right now, darwaza tootne wala hai please police bhejo jaldi.", "language": "Hinglish", "risk_level": "CRITICAL", "reason": "Door breach imminent in life-threatening attack."},
    {"text": "Mujhe turant rescue support chahiye, situation out of hand hai bilkul.", "language": "Hinglish", "risk_level": "CRITICAL", "reason": "Critical rescue request."},
    {"text": "Main apne aap ko safe nahi rakh sakta is halat me, please help.", "language": "Hinglish", "risk_level": "CRITICAL", "reason": "Inability to maintain personal safety."},
    {"text": "Unke paas lethal weapons hain aur wo ghar me ghusne ki koshish kar rahe hain.", "language": "Hinglish", "risk_level": "CRITICAL", "reason": "Armed intruders attempting home entry."},
    {"text": "Emergency call connect karo immediately, jaan ko khatra hai.", "language": "Hinglish", "risk_level": "CRITICAL", "reason": "Immediate danger to life requesting emergency call."},
    {"text": "Main hide hokar message kar raha hoon, wo mujhe maar dalenge agar dekha toh.", "language": "Hinglish", "risk_level": "CRITICAL", "reason": "Hiding in immediate mortal peril."},

    # Marathi CRITICAL
    {"text": "मला आत्ता अजिबात सुरक्षित वाटत नाहीये. मला तातडीने मदतीची गरज आहे, मी एकटा आहे.", "language": "Marathi", "risk_level": "CRITICAL", "reason": "Feeling unsafe and demanding immediate help in Marathi."},
    {"text": "मला भीती वाटते की मी स्वतःला सुरक्षित ठेवू शकणार नाही, कृपया त्वरित मदत करा.", "language": "Marathi", "risk_level": "CRITICAL", "reason": "Inability to maintain personal safety in Marathi."},
    {"text": "माझ्या जीवावर बेतले आहे, काही लोक हत्यारे घेऊन माझ्या दारात उभे आहेत.", "language": "Marathi", "risk_level": "CRITICAL", "reason": "Armed individuals at doorstep threatening life."},
    {"text": "मला तातडीने संरक्षण द्या, माझ्यावर हिंसक हल्ला झाला आहे आणि मी जखमी आहे.", "language": "Marathi", "risk_level": "CRITICAL", "reason": "Violent assault resulting in injury."},
    {"text": "मी सुरक्षित नाही आणि कोणत्याही क्षणी माझ्यावर हल्ला होऊ शकतो.", "language": "Marathi", "risk_level": "CRITICAL", "reason": "Imminent violent attack threat."},
    {"text": "कृपया पोलिसांना ताबडतोब पाठवा, माझा जीव धोक्यात आहे.", "language": "Marathi", "risk_level": "CRITICAL", "reason": "Immediate police dispatch request for life threat."},
    {"text": "घरात मारहाण सुरू आहे आणि मी मुलाला घेऊन एका खोलीत लपून बसलो आहे.", "language": "Marathi", "risk_level": "CRITICAL", "reason": "Active domestic assault with infant hiding."},
    {"text": "माझ्या जिवाला गंभीर धोका निर्माण झाला आहे, तातडीने बचाव पथक पाठवावे.", "language": "Marathi", "risk_level": "CRITICAL", "reason": "Grave life danger requiring rescue team."},
    {"text": "स्वतःचा बचाव करणे माझ्यासाठी अशक्य झाले आहे.", "language": "Marathi", "risk_level": "CRITICAL", "reason": "Inability to defend or protect oneself."},
    {"text": "हा जीवन आणि मृत्यूचा प्रश्न आहे, त्वरित ऑपरेटरशी बोलायचे आहे.", "language": "Marathi", "risk_level": "CRITICAL", "reason": "Life and death crisis requiring immediate operator."},
    {"text": "मला जिवंत राहण्याची भीती वाटत आहे, कृपया मला येथून सुरक्षित बाहेर काढा.", "language": "Marathi", "risk_level": "CRITICAL", "reason": "Urgent evacuation request from lethal threat."},

    # Romanized Marathi CRITICAL
    {"text": "Mala atta safe vatat nahiye, immediate help havi ahe mala.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "reason": "Feeling unsafe requiring immediate help in Romanized Marathi."},
    {"text": "Mala bhiti ahe ki mi swatala safe thevu shaknar nahi ya situation madhe.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "reason": "Inability to maintain self safety in Romanized Marathi."},
    {"text": "Majhya jeevala khoop motha dhoka ahe, police la bolva lagech.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "reason": "Severe life threat requesting immediate police."},
    {"text": "Majhyavar attack zala ahe ani mi raktbambal ahe, ambulance pathva.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "reason": "Physical attack with severe bleeding needing ambulance."},
    {"text": "Te lok mala marun taknar ahet, mi bathroom madhe laplo ahe.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "reason": "Hiding from mortal threat in bathroom."},
    {"text": "Mi safe nahi ahe ithe, please mala rescue kara emergency madhe.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "reason": "Emergency rescue plea from unsafe location."},
    {"text": "Swatachi safety thevna mala jamat nahiye khoop extreme problem ahe.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "reason": "Extreme crisis inability to stay safe."},
    {"text": "Darwaja thokat ahet te gund, please konatari officer pathva fast.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "reason": "Goons pounding on door, urgent intervention needed."},
    {"text": "Gharat aag lavnyacha prayatna kela ahe, amcha jeev vachva.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "reason": "Arson attempt endangering lives."},
    {"text": "Life and death cha question ahe, human operator shi connect kara.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "reason": "Life and death question connecting to operator."},
    {"text": "Mi swatala safe nahi thevu shakat, help urgently.", "language": "Romanized Marathi", "risk_level": "CRITICAL", "reason": "Direct expression of safety inability."},

    # Mixed CRITICAL
    {"text": "I do not feel safe right now, mujhe turant help chahiye please send police.", "language": "Mixed", "risk_level": "CRITICAL", "reason": "Mixed safety emergency demanding police."},
    {"text": "I am worried that I may not be able to keep myself safe, bohot darr lag raha hai.", "language": "Mixed", "risk_level": "CRITICAL", "reason": "Safety inability with intense terror."},
    {"text": "Some men are trying to break my window, mala vachva please immediately.", "language": "Mixed", "risk_level": "CRITICAL", "reason": "Break-in in progress plea for rescue."},
    {"text": "I am under severe physical threat, meri jaan khatre mein hai.", "language": "Mixed", "risk_level": "CRITICAL", "reason": "Severe physical threat and life in danger."},
    {"text": "They attacked my house with weapons, aamcha jeev dhokyat ahe urgently intervene.", "language": "Mixed", "risk_level": "CRITICAL", "reason": "Armed house attack endangering life."},
    {"text": "I cannot stay safe here, mujhe lagta hai aaj raat main zinda nahi bachunga.", "language": "Mixed", "risk_level": "CRITICAL", "reason": "Mortal dread of not surviving the night."},
    {"text": "My ex-partner is outside with a knife, please emergency team bhejo abhi ke abhi.", "language": "Mixed", "risk_level": "CRITICAL", "reason": "Immediate armed domestic stalking threat."},
    {"text": "Mala atta safe vatat nahiye, I need urgent human operator escalation right now.", "language": "Mixed", "risk_level": "CRITICAL", "reason": "Unsafe statement requesting immediate human escalation."},
    {"text": "I am bleeding heavily after a robbery, please ambulance aur police urgently bhejo.", "language": "Mixed", "risk_level": "CRITICAL", "reason": "Armed robbery with heavy bleeding requiring ambulance."},
    {"text": "The threat is immediate and real, main kisi bhi pal attack ho sakta hoon.", "language": "Mixed", "risk_level": "CRITICAL", "reason": "Immediate real threat of violence."},
    {"text": "Emergency situation, I am unable to protect myself and my mother, please rescue us.", "language": "Mixed", "risk_level": "CRITICAL", "reason": "Inability to protect vulnerable family member requiring rescue."},
]

def main():
    print(f"Total raw examples defined: {len(RAW_DATA)}")
    
    # Assign unique systematic IDs
    dataset = []
    class_counts = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
    lang_counts = {}

    for idx, item in enumerate(RAW_DATA, 1):
        record = {
            "id": f"COMP-{idx:03d}",
            "text": item["text"].strip(),
            "language": item["language"],
            "risk_level": item["risk_level"],
            "reason": item["reason"],
        }
        dataset.append(record)
        class_counts[item["risk_level"]] += 1
        lang_counts[item["language"]] = lang_counts.get(item["language"], 0) + 1

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(dataset)} examples to {DATA_FILE}")
    print("Class Distribution:")
    for k, v in class_counts.items():
        print(f"  {k}: {v} ({round(v/len(dataset)*100, 1)}%)")
    print("Language Distribution:")
    for k, v in sorted(lang_counts.items()):
        print(f"  {k}: {v} ({round(v/len(dataset)*100, 1)}%)")

if __name__ == "__main__":
    main()

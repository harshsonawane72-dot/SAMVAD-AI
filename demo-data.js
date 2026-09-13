/**
 * SAMVAD AI — fictional / demo data only
 * Used to populate statements, cases, and dashboard without a backend.
 * No real names, phone numbers, addresses, or identifying information.
 */

const DEMO_DATA = {
  sampleStatements: [
    "Mujhe apni complaint ke process ke baare mein information chahiye. Main thoda worried hoon.",
    "Mujhe kaafi stress ho raha hai aur mujhe samajh nahi aa raha ki complaint ko kaise proceed karun. Mujhe support chahiye.",
    "Mujhe bahut fear aur pressure feel ho raha hai. Mujhe lag raha hai ki main is situation ko akela handle nahi kar pa raha/rahi. Mujhe jaldi support chahiye.",
    "Mujhe abhi safe feel nahi ho raha. Mujhe immediate help chahiye aur main situation ko akela handle nahi kar sakta/sakti.",
  ],
  sampleCases: [
    {
      id: "NHAA-2026-1042",
      datetime: "11 Sep 2026, 6:42 PM",
      time: "18:42",
      language: "Hindi",
      interaction: "Chat",
      status: "New",
      statement:
        "Mujhe apni complaint ke process ke baare mein information chahiye. Main thoda worried hoon.",
      createdAt: "2026-09-11T13:12:00.000Z",
    },
    {
      id: "NHAA-2026-1108",
      datetime: "11 Sep 2026, 5:15 PM",
      time: "17:15",
      language: "English",
      interaction: "Portal",
      status: "Reviewed",
      statement:
        "I need information about how to file my complaint. I am a little worried about the process.",
      createdAt: "2026-09-11T11:45:00.000Z",
    },
    {
      id: "NHAA-2026-1186",
      datetime: "11 Sep 2026, 7:08 PM",
      time: "19:08",
      language: "Hindi",
      interaction: "Chat",
      status: "Under Review",
      statement:
        "Mujhe kaafi stress ho raha hai aur mujhe samajh nahi aa raha ki complaint ko kaise proceed karun. Mujhe support chahiye.",
      createdAt: "2026-09-11T13:38:00.000Z",
    },
    {
      id: "NHAA-2026-1214",
      datetime: "11 Sep 2026, 4:51 PM",
      time: "16:51",
      language: "English",
      interaction: "Voice",
      status: "New",
      statement:
        "I am feeling stressed and somewhat helpless. I need support to understand the next steps.",
      createdAt: "2026-09-11T11:21:00.000Z",
    },
    {
      id: "NHAA-2026-1301",
      datetime: "11 Sep 2026, 8:02 PM",
      time: "20:02",
      language: "Hindi",
      interaction: "Chat",
      status: "Under Review",
      statement:
        "Mujhe bahut fear aur pressure feel ho raha hai. Mujhe lag raha hai ki main is situation ko akela handle nahi kar pa raha/rahi. Mujhe jaldi support chahiye.",
      createdAt: "2026-09-11T14:32:00.000Z",
    },
    {
      id: "NHAA-2026-1360",
      datetime: "11 Sep 2026, 3:27 PM",
      time: "15:27",
      language: "Marathi",
      interaction: "IVRS",
      status: "New",
      statement:
        "I feel a lot of fear and pressure. I am alone and unable to cope. I need help quickly.",
      createdAt: "2026-09-11T09:57:00.000Z",
    },
    {
      id: "NHAA-2026-1422",
      datetime: "11 Sep 2026, 8:19 PM",
      time: "20:19",
      language: "Hindi",
      interaction: "Chat",
      status: "New",
      statement:
        "Mujhe abhi safe feel nahi ho raha. Mujhe immediate help chahiye aur main situation ko akela handle nahi kar sakta/sakti.",
      createdAt: "2026-09-11T14:49:00.000Z",
    },
    {
      id: "NHAA-2026-1477",
      datetime: "11 Sep 2026, 2:11 PM",
      time: "14:11",
      language: "English",
      interaction: "Voice",
      status: "Under Review",
      statement:
        "I do not feel safe right now. I need immediate help. I cannot stay safe and I am alone.",
      createdAt: "2026-09-11T08:41:00.000Z",
    },
  ],
  supportOptions: [
    "Information and general support",
    "Counselling / support referral recommended",
    "Priority human review and appropriate counselling/legal support referral",
    "Immediate human review and appropriate emergency/protection support pathway",
  ],
};

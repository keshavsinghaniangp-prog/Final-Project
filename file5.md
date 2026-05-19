# 🛡️ The Database Detective: How Our Security System Works!

Imagine you are a detective guarding a giant library full of super-secret information (like people's salaries, passwords, and bank details). 

This library is called a **Database**, and the people reading the books are **Users**. Most users are just doing their normal jobs. But what if a bad guy sneaks in, or a normal user decides to steal a bunch of books in the middle of the night? 

That's where our **Enterprise DAM System** comes in! It’s a super-smart robot detective that watches every single thing people do in the library to make sure nobody is breaking the rules.

Here is a simple guide to how our robot detective works and where all its parts live!

---

## 🗺️ The Detective's Office (Where Everything Lives)

Our project is organized into different folders, kind of like rooms in a police station:

*   **`app.py` (The Front Desk)**: This is the main screen you see when you turn on the system. It shows the big numbers: How many people are in the library right now, and how many alarms are ringing.
*   **`pages/` (The Investigation Rooms)**:
    *   **`1_User_Monitoring.py`**: This is the "Leaderboard of Suspects." It ranks everyone in the library from safest (Green) to most dangerous (Red).
    *   **`2_Dashboard.py`**: This is where we put a magnifying glass on *one specific person* to see exactly what books they looked at and when.
    *   **`3_Alerts.py`**: The flashing red alarm center! If someone does something really bad, a siren goes off here.
*   **`model/` (The Robot's Brain)**: This folder holds the `unusual_query_detector.pkl` file. This is the actual saved "brain" of our Machine Learning robot.
*   **`data/` (The Security Camera Tapes)**: This holds the `1200_rows.csv` file, which is a giant list of every single action every user took.

---

## 🧠 The Robot Brain (Machine Learning)

How does the detective know if someone is acting weird? We use **Machine Learning (ML)**! Specifically, a type of math called a **Random Forest**. 

Imagine 100 tiny detectives (trees) sitting in a room. 
1. The robot looks at a user's action (like "User_01 downloaded 800 salary files at 3:00 AM").
2. It asks all 100 tiny detectives: "Is this weird?"
3. If the majority of them vote "Yes! That's weird!", the robot throws a red flag.

When you start the app, a helper file called `utils/data_loader.py` grabs the security tapes (the CSV data) and feeds them into the Robot Brain *live*, so the app always knows who the bad guys are right now!

---

## 🧮 The Suspect Scoreboard (How We Grade Danger)

In the **User Monitoring** room (`pages/1_User_Monitoring.py`), everyone gets a "Danger Score" from 0 to 100. 100 means you are definitely a bad guy. 0 means you are a perfect angel. 

Here is how the math works to give you a score:

1.  **Count the Crimes**: First, we count up all the suspicious things you did. Did you fail your password 5 times? Did you download way too much data? Did the Robot Brain flag you?
2.  **Compare to the Worst Guy**: If we just counted crimes, someone who works 12 hours a day might look like a bad guy just because they do a lot of stuff. So, we compare you to the *worst* offender in the building. If the worst guy stole 10 books, and you stole 4, you get a 40% score for stealing.
3.  **Weigh the Crimes**: Some crimes are worse than others!
    *   🤖 **The Robot Brain flagging you** gives you a TON of bad points (50%).
    *   🔐 **Failing your password** gives you a good amount of bad points (20%).
    *   👀 **Looking at secret files** gives you a good amount of bad points (20%).
    *   🌙 **Working in the middle of the night** gives you a bit of bad points (10%).

If your total score goes over **70**, you get a 🔴 **Red High-Risk Badge**, and the security guards are called!

---

## 🚨 The Alarm System (Alerts Center)

In the **Alerts Center** (`pages/3_Alerts.py`), the system pops up boxes with sirens depending on what rule you broke:

*   **CRITICAL (Big Trouble! 🛑)**: You get a Critical alert if the Robot Brain catches you doing something super weird.
*   **WARNING (Watch Out! ⚠️)**: You get a Warning if you keep messing up your password, or if you decide to snoop around the sensitive salary files in the middle of the night.

## 🚀 How to Turn On the Detective!

If you want to boot up the system and see the detective in action, you just need to tell your computer to run this simple command:

```powershell
py -m streamlit run app.py
```

And BOOM! The detective is online and watching the database!
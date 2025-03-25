import autogen
import panel as pn
import os
import time
import asyncio
from typing import List, Dict
import logging
from src import globals
from src.FSMs.fsm_career_path_interest import CareerFSM
from src.Agents.group_chat_manager_agent import CustomGroupChatManager, CustomGroupChat
from src.UI.reactive_chat_vt import ReactiveChat
from src.UI.avatar import avatar
from enum import Enum
from dotenv import load_dotenv
from transitions import Machine
from src.Agents.learner_model_agent import LearnerModelAgent
from src.Agents.tutor_agent import TutorAgent


load_dotenv()

logging.basicConfig(level=logging.INFO, 
                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

os.environ["AUTOGEN_USE_DOCKER"] = "False"

###############################################
# ChatGPT Model
###############################################

gpt4_config_list = [{'model': "gpt-4o"}]

temperature = 0
max_tokens = 1000
top_p = 0.5
frequency_penalty = 0.1
presence_penalty = 0.1
seed = 53

gpt4_config = {
    "config_list": gpt4_config_list, 
    "temperature": temperature,
    "max_tokens": max_tokens,
    "top_p": top_p,
    "frequency_penalty": frequency_penalty,
    "presence_penalty": presence_penalty,
    "seed": seed
}

llm = gpt4_config

#################################################
# Define Agents
#################################################
from src.Agents.student_agent import StudentAgent
from src.Agents.career_growth_agent import CareerGrowthAgent
from src.Agents.certification_recommendation_agent import CertificationRecommendationAgent
from src.Agents.job_finder_agent import JobFinderAgent
from src.Agents.agents import AgentKeys

# Instantiate agents
student = StudentAgent(llm_config=llm)
career_growth = CareerGrowthAgent(llm_config=llm)
cert_recommendation = CertificationRecommendationAgent(llm_config=llm)
job_finder = JobFinderAgent(llm_config=llm)
learner_model = LearnerModelAgent(llm_config=llm)
tutor = TutorAgent(llm_config=llm)



agents_dict = {
    AgentKeys.STUDENT.value: student,
    AgentKeys.CAREER_GROWTH.value: career_growth,
    AgentKeys.CERTIFICATION_RECOMMENDATION.value: cert_recommendation,
    AgentKeys.JOB_FINDER.value: job_finder,
    AgentKeys.LEARNER_MODEL.value: learner_model,
    AgentKeys.TUTOR.value: tutor
}

avatars = {
    student.name: "✏️",  
    career_growth.name: "🚀",
    cert_recommendation.name: "🎓",
    job_finder.name: "🎯",
    learner_model.name: "🧠",
    tutor.name: "🧑‍🎓",
}

##############################################
# Main Adaptive Learning Application
############################################## 
globals.input_future = None
script_dir = os.path.dirname(os.path.abspath(__file__))
progress_file_path = os.path.join(script_dir, '../../progress.json')



class CareerFSM:
    states = ["start", "student_interaction", "career_guidance", "cert_recommendation", 
              "job_search", "final"]

    def __init__(self, agents_dict):
        self.machine = Machine(model=self, states=CareerFSM.states, initial="start")

        # Define transitions
        self.machine.add_transition("begin_interaction", "start", "student_interaction")
        self.machine.add_transition("guide", "student_interaction", "career_guidance")
        self.machine.add_transition("recommend_certifications", "career_guidance", "cert_recommendation")
        self.machine.add_transition("find_jobs", "cert_recommendation", "job_search")
        self.machine.add_transition("complete", "job_search", "final")

        self.agents_dict = agents_dict
        self.current_speaker_index = 0
        self.agent_names = list(agents_dict.keys())

    def next_speaker_selector(self):
        """Selects the next agent in the conversation cycle."""
        print(f"Current speaker cycle: {self.agent_names}")  # ✅ Debugging
        next_speaker = self.agent_names[self.current_speaker_index]
        self.current_speaker_index = (self.current_speaker_index + 1) % len(self.agent_names)
        return self.agents_dict[next_speaker]
    
    def register_groupchat_manager(self, manager):
        """Assigns the group chat manager to FSM."""
        self.groupchat_manager = manager



# Initialize FSM
fsm = CareerFSM(agents_dict)
fsm.agent_names = list(agents_dict.keys())

# ✅ Start FSM manually if needed:
fsm.begin_interaction()




groupchat = CustomGroupChat(
    agents=list(agents_dict.values()), 
    messages=[],
    max_round=globals.MAX_ROUNDS,
    send_introductions=True,
    speaker_selection_method=fsm.next_speaker_selector,
)

manager = CustomGroupChatManager(
    groupchat=groupchat,
    filename=progress_file_path, 
    is_termination_msg=lambda x: x.get("content", "").rstrip().find("TERMINATE") >= 0, 
    
)    

fsm.register_groupchat_manager(manager)

# Begin GUI components
reactive_chat = ReactiveChat(agents_dict=agents_dict, avatars=avatars, groupchat_manager=manager)

# Register groupchat_manager and reactive_chat with agents
for agent in groupchat.agents:
    agent.groupchat_manager = manager
    agent.reactive_chat = reactive_chat
    agent.register_reply([autogen.Agent, None], reply_func=agent.autogen_reply_func, config={"callback": None})
    print(f"Registered reply handler for: {agent.name}")  # ✅ Debugging



# Load chat history on startup
manager.get_chat_history_and_initialize_chat(filename=progress_file_path, chat_interface=reactive_chat.learn_tab_interface)
reactive_chat.update_dashboard()  # Call after history is loaded

##############################################
# UI Handlers
##############################################

# Career Progression Plan
async def handle_button_career_progress(event=None):
    """
    Request a career progression plan from Career Growth Agent.
    """
    await a_get_career_progress()

async def a_get_career_progress():
    """
    Ask the Career Growth Agent to generate a step-by-step career plan.
    """
    await career_growth.a_send("Generate a career progression plan for the student.", recipient=career_growth, request_reply=True)

    response = career_growth.last_message(agent=career_growth)["content"]
    print(f"Agent response: {response}")  # ✅ Debugging
    
    reactive_chat.model_tab_interface.send(response, user=career_growth.name, avatar=avatars[career_growth.name])


# Certification Recommendations
async def handle_button_cert_recommendations(event=None):
    """
    Request certification recommendations from Certification Recommendation Agent.
    """
    await a_get_cert_recommendations()

async def a_get_cert_recommendations():
    """
    Ask the Certification Recommendation Agent to provide certification suggestions.
    """
    await cert_recommendation.a_send("Provide certification recommendations for the student.", recipient=cert_recommendation, request_reply=True)

    response = cert_recommendation.last_message(agent=cert_recommendation)["content"]
    
    reactive_chat.model_tab_interface.send(response, user=cert_recommendation.name, avatar=avatars[cert_recommendation.name])

# Job Finder
async def handle_find_jobs(event=None):
    """
    Request job recommendations from ChatGPT through JobFinderAgent.
    """
    await a_find_jobs()

async def a_find_jobs():
    """
    Get real-time job suggestions based on student capabilities.
    """
    await job_finder.a_send("Provide job recommendations for the student.", recipient=job_finder, request_reply=True)

    response = job_finder.last_message(agent=job_finder)["content"]
    
    reactive_chat.model_tab_interface.send(response, user=job_finder.name, avatar=avatars[job_finder.name])

##############################################
# Panel UI Setup
############################################## 

# --- Add UI Buttons ---
reactive_chat.button_career_progress = pn.widgets.Button(
    name="Get Career Progression Plan", button_type="primary"
)
reactive_chat.button_career_progress.on_click(handle_button_career_progress)

reactive_chat.button_cert_recommendations = pn.widgets.Button(
    name="Get Certification Suggestions", button_type="primary"
)
reactive_chat.button_cert_recommendations.on_click(handle_button_cert_recommendations)

reactive_chat.button_find_jobs = pn.widgets.Button(
    name="Find Jobs", button_type="primary"
)
reactive_chat.button_find_jobs.on_click(handle_find_jobs)

# --- Career Progression Tab ---
career_progression_tab = (
    "Career Progression", 
    pn.Column(
        pn.Row(reactive_chat.button_career_progress),
        pn.Row(reactive_chat.button_cert_recommendations),
        pn.Row(reactive_chat.model_tab_interface)
    )
)

# --- Career Finder Tab ---
career_finder_tab = (
    "Career Finder", 
    pn.Column(
        pn.Row(reactive_chat.button_find_jobs),
        pn.Row(reactive_chat.model_tab_interface)
    )
)

# Create Panel UI
def create_app():
    return pn.Tabs(
        career_progression_tab,
        career_finder_tab
    )

if __name__ == "__main__":
    app = create_app()
    pn.serve(app, callback_exception="verbose")

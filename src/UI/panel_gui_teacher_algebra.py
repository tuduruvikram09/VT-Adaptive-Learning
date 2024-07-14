###############################################################################
#
# Teacher Algebra Use Case Description
#
# Use-Case Name: Teacher Algebra
# Use Case Type: Primary
# Primary Actor: Teacher Agent
#
# Stakeholders and Interests
#   - Other Agents: Student, Tutor, Knowledge Tracer, Problem Generator, 
#                   Solution Verifier, Learner Model, Level Adapter, Motivator
#
# Description: This use-case describes TeacherAgent is responsible for creating 
# and delivering educational content. When given a subject, the TeacherAgent prepares 
# teaching materials and delivers content in a format that suits the student's preferences.
# 
# Trigger: The TeacherAgent's interaction with the student is more structured and planned, 
# focusing on teaching specific subjects or topics in a systematic way.
# Type: External
# Relationships:  Note - TBD. Will be filled in later. There are lots of them.
#    Association: Student, Teacher
#    Include: Provide Personalized Lessons, Assess Understanding, Recommend Resources
#    Extend: Address Student Questions
#    Generalization:  None
#
# Normal Flow of Events:
# 1. The student requests help with algebra or the scheduled algebra lesson begins.
# 2. The teacher agent greets the student and asks for any specific topics or problems they need help with.
# 3. The student specifies a topic or problem.
# 4. The teacher agent provides an explanation of the topic or step-by-step solution to the problem.
# 5. The teacher agent checks for understanding by asking follow-up questions.
# 6. The student responds to the follow-up questions.
# 7. The teacher agent provides feedback based on the student's responses.
# 8. The teacher agent recommends additional resources if necessary.
# 9. The session ends with a summary of what was covered and suggestions for further study.
#
# SubFlows:
# S-1: If the student does not specify a topic or problem, the teacher agent provides a general overview of key algebra concepts.
#
# Alternate/Exceptional Flows:
# A-1: If the student is unable to understand the explanation, the teacher agent provides alternative explanations or examples.
# A-2: If the student encounters technical issues, the teacher agent provides instructions to resolve them or reschedules the session.
#
###############################################################################


import autogen
import panel as pn
import openai
import os
import time
import asyncio
from typing import List, Dict
import logging
from src import globals
from src.UI.avatar import avatar

os.environ["AUTOGEN_USE_DOCKER"] = "False"

globals.input_future = None


############################################################################################
#
#  DEFINE AGENTS
#
############################################################################################
from ..Agents.base_agent import MyBaseAgent
from ..Agents.conversable_agent import MyConversableAgent
from ..Agents.student_agent import StudentAgent
from ..Agents.knowledge_tracer_agent import KnowledgeTracerAgent
from ..Agents.teacher_agent import TeacherAgent
from ..Agents.tutor_agent import TutorAgent
from ..Agents.problem_generator_agent import ProblemGeneratorAgent
from ..Agents.solution_verifier_agent import SolutionVerifierAgent
from ..Agents.programmer_agent import ProgrammerAgent
from ..Agents.code_runner_agent import CodeRunnerAgent
from ..Agents.learner_model_agent import LearnerModelAgent
from ..Agents.level_adapter_agent import LevelAdapterAgent
from ..Agents.motivator_agent import MotivatorAgent
from ..Agents.group_chat_manager_agent import CustomGroupChatManager


# Agents
#####################################################################################
# I've set all the Agents to the prompts found to be "best" in Sprint-2
# 
# Below are examplex of how to override defaults in this file instead of agent file
#
# I believe these are the only 3 you will need to change
#
# If you find otherwise, you will need to directly update the agents
#    becasue I only created constructors for these additional parameters
#
# See the README.md file for description vs system_message
##########################################################################

#######################################
# Student was not completed in Sprint-2
#######################################
student_description = """StudentAgent aims to learn and understand new concepts.
                 StudentAgent actively listens to the Teacher, asks relevant questions, and seeks additional information when needed.
                 StudentAgent is curious, attentive, and eager to grasp the material presented.
                 """

student_system_message = """StudentAgent's task is to actively engage in learning by listening to the Teacher, asking relevant questions, and seeking additional information to fully understand new concepts.
                 """

student = StudentAgent(
    human_input_mode='ALWAYS',
    description=student_description,
    system_message=student_system_message     
)


###################
# Knowledge Tracer
##################
kt_description = """You are a Knowledge Tracer.
                    You test the student on what they know.
                    You work with the Problem Generator to present problems to the Student.
                    You work with the Learner Model to keep track of the Student's level.
            """
knowledge_tracer = KnowledgeTracerAgent(
    human_input_mode='ALWAYS',
    description=kt_description,
    system_message=kt_description    
)

###################
# Teacher
###################
t_description = """TeacherAgent presents new material in a clear and concise manner, focusing on delivering lecture-type content when asked by the Student.
                 """
t_system_message = """TeacherAgent's task is to provide clear and concise lecture-type material when the Student asks to learn new concepts.
                 """

teacher = TeacherAgent(
    human_input_mode='NEVER',
    description=t_description,
    system_message=t_system_message     
)


###################
# Tutor
###################
tut_description = """  TutorAgent is designed to assist students in real-time with their math problems. It offers solutions and explanations, responding effectively to inquiries to support adaptive learning. TutorAgent's goal is to make learning easier and more interactive for students.
                        """
tutor = TutorAgent(
    human_input_mode='NEVER',
    description=tut_description,
    system_message=tut_description      
)

###################
# Problem Generator
###################
pg_description = """ProblemGenerator is designed to generate mathematical problems based on the current curriculum and the student's learning level.
                ProblemGenerator ensures that the problems generated are appropriate and challenging."""
                    
pg_system_message = """ProblemGenerator will generate mathematical problems based on the current curriculum and the student's learning level.
                        ProblemGenerator ensures that the problems generated are appropriate and challenging."""

problem_generator = ProblemGeneratorAgent(
    human_input_mode='NEVER',
    description=pg_description,
    system_message=pg_system_message     
)

###################
# Solution Verifier
###################
sv_description = """SolutionVerifierAgent ensures the accuracy of solutions provided for various problems. SolutionVerifierAgent checks solutions against the correct answers and offers feedback on their correctness."""
    
sv_system_message = """SolutionVerifierAgent's task is to verify the correctness of solutions submitted by comparing them against the correct answers and providing feedback on their accuracy."""

solution_verifier = SolutionVerifierAgent(
    human_input_mode='ALWAYS',
    description=sv_description,
    system_message=sv_description     
)

###########################################
# Programmer was not completed in Sprint-2
###########################################
p_description = """You are a Programmer.
                 Your role is to write, debug, and optimize code based on the given requirements.
                 You approach problems methodically, breaking them down into manageable tasks.
                 You continuously seek to improve the efficiency and functionality of the software you develop.
                 """
programmer = ProgrammerAgent(
    human_input_mode='NEVER',
    description=p_description,
    system_message=p_description     
)

###################
# Code Runner
###################
cr_description = """As a vital component of a collaborative agent framework, Code Runner specializes in executing and displaying code outputs. Code Runner interacts seamlessly with educational and development agents, enhancing learning and programming experiences. By providing real-time feedback on code execution, Code Runner support users and other agents in refining and understanding complex code segments, contributing to a more robust and interactive learning environment."""
cr_system_message = """Code Runner's function is to execute and display code outputs, providing real-time feedback. Code Runner interacts seamlessly with educational and development agents, enhancing learning and programming experiences. By refining and understanding complex code segments, Code Runner supports users and other agents, contributing to a more robust and interactive learning environment. """
code_runner = CodeRunnerAgent(
    human_input_mode='NEVER',
    description=cr_description,
    system_message=cr_system_message  
)

###################
# Level Adapter
###################
lv_description ="""
    LevelAdapter is an agent that interacts with the Learner Model to fetch information about the Student's learning progress.
    LevelAdapter provides input to other agents or systems based on the Student's level.
    """    
lv_system_message ="""
    LevelAdapter is ready to interact with the Learner Model to provide information about the Student's learning progress.
    LevelAdapter can provide input to other agents or systems based on the Student's level.
    """
level_adapter = LevelAdapterAgent(
    human_input_mode='NEVER',
    description=lv_description,
    system_message=lv_system_message   
)

###################
# Motivator
###################
m_description = """ You provide positive and encouraging feedback to the Student to keep them motivated.
                        Only provide motivation to the Student. 
                        Offer specific praise and acknowledge the Student's effort and progress.
                        Do not provide motivating comments to any other agent except the Student.
                        """
motivator = MotivatorAgent(
    human_input_mode='NEVER',
    description=m_description,
    system_message=m_description  
)

###################
# Level Model
###################
lm_description="""Learner Model is a diligent and meticulous learning tracker. Learner Model assess the Student's educational journey, adapting learning paths by collaborating with the Tutor and Knowledge Tracer. Learner Model analyzes performance data to provide feedback, help set educational goals, and adjust the difficulty of tasks. Learner Model ensures that the learning experience is tailored to the Student’s evolving capabilities and needs."""
lm_system_message="""Learner Model's function is to diligently track the Student's educational journey. Learner Model assesses performance data, collaborates with the Tutor and Knowledge Tracer, and adapts learning paths to provide feedback. Learner Model helps set educational goals and adjusts the difficulty of tasks, ensuring that the learning experience is tailored to the Student’s evolving capabilities and needs. """        
learner_model = LearnerModelAgent(
    human_input_mode='ALWAYS',
    description=lm_description,
    system_message=lm_system_message
)




agents_dict = {
    "student": student,
    "knowledge_tracer": knowledge_tracer,
    "teacher": teacher,
    "tutor": tutor,
    "problem_generator": problem_generator,
    "solution_verifier": solution_verifier,
    "programmer": programmer,
    "code_runner": code_runner,
    "learner_model": learner_model,
    "level_adapter": level_adapter,
    "motivator": motivator
}


####################################################################################################
#
#  Define Agent Transitions: Unconstrained, Allowed, or Disallowed
#
####################################################################################################
TRANSITIONS = 'DISALLOWED'      # Set TRANSITIONS for type
if TRANSITIONS == 'DISALLOWED':

    disallowed_agent_transitions = {
        student: [solution_verifier, programmer, code_runner, learner_model, level_adapter, motivator],
        tutor: [programmer, code_runner],
        teacher: [solution_verifier,knowledge_tracer, programmer, code_runner, learner_model, level_adapter, motivator],
        knowledge_tracer: [teacher, tutor, motivator],
        problem_generator: [teacher, solution_verifier, programmer, code_runner, motivator],
        solution_verifier: [student, teacher, problem_generator, learner_model, level_adapter, motivator],
        programmer: [student, tutor, teacher, knowledge_tracer, learner_model, level_adapter, motivator],
        code_runner: [student, teacher, tutor, knowledge_tracer, problem_generator, learner_model, level_adapter, motivator],
        learner_model: [student, teacher, problem_generator, solution_verifier, programmer, code_runner],
        level_adapter: [student, teacher, solution_verifier, programmer, code_runner, motivator],
        motivator: [tutor, teacher, knowledge_tracer, problem_generator, solution_verifier, programmer, code_runner, learner_model, level_adapter]
    }
    groupchat = autogen.GroupChat(agents=list(agents_dict.values()), 
                                messages=[],
                                max_round=40,
                                send_introductions=True,
                                speaker_transitions_type="disallowed",
                                allowed_or_disallowed_speaker_transitions=disallowed_agent_transitions,
                                )
    
elif TRANSITIONS == 'ALLOWED':
    allowed_agent_transitions = {
        student: [tutor],
        tutor: [student, teacher, problem_generator, solution_verifier, motivator],
        teacher: [student, tutor, problem_generator,learner_model],
        knowledge_tracer: [student, problem_generator, learner_model, level_adapter],
        problem_generator: [tutor],
        solution_verifier: [programmer],
        programmer: [code_runner],
        code_runner: [tutor, solution_verifier],
        learner_model: [knowledge_tracer, level_adapter],
        level_adapter: [tutor, problem_generator, learner_model],
        motivator: [tutor]
    }
    groupchat = autogen.GroupChat(agents=list(agents_dict.values()), 
                              messages=[],
                              max_round=40,
                              send_introductions=True,
                              speaker_transitions_type="allowed",
                              allowed_or_disallowed_speaker_transitions=allowed_agent_transitions,
                               )

else:  # Unconstrained
    agents = list(agents_dict.values()) # All agents
    groupchat = autogen.GroupChat(agents=agents, 
                              messages=[],
                              max_round=40,
                              send_introductions=True,
                              )





manager = CustomGroupChatManager(groupchat=groupchat)

####################################################################################
#
# Application Code
#
####################################################################################

# --- Panel Interface ---
def create_app():
    # --- Panel Interface ---
    pn.extension(design="material")


    async def callback(contents: str, user: str, instance: pn.chat.ChatInterface):
        if not globals.initiate_chat_task_created:
            asyncio.create_task(manager.delayed_initiate_chat(tutor, manager, contents))  
        else:
            if globals.input_future and not globals.input_future.done():
                globals.input_future.set_result(contents)
            else:
                print("No input being awaited.")


    chat_interface = pn.chat.ChatInterface(callback=callback)

    def print_messages(recipient, messages, sender, config):
        print(f"Messages from: {sender.name} sent to: {recipient.name} | num messages: {len(messages)} | message: {messages[-1]}")

        content = messages[-1]['content']

        if all(key in messages[-1] for key in ['name']):
            chat_interface.send(content, user=messages[-1]['name'], avatar=avatar[messages[-1]['name']], respond=False)
        else:
            chat_interface.send(content, user=recipient.name, avatar=avatar[recipient.name], respond=False)
        
        return False, None  # required to ensure the agent communication flow continues

    # Register chat interface with ConversableAgent
    for agent in groupchat.agents:
        agent.chat_interface = chat_interface
        agent.register_reply([autogen.Agent, None], reply_func=print_messages, config={"callback": None})

    # Create the Panel app object with the chat interface
    app = pn.template.BootstrapTemplate(title=globals.APP_NAME)
    app.main.append(
        pn.Column(
            chat_interface
        )
    )
    chat_interface.send("Welcome to the Adaptive Math Teacher! How can I help you today?", user="System", respond=False)
    
    return app


if __name__ == "__main__":
    app = create_app()
    #pn.serve(app, debug=True)
    pn.serve(app)
 
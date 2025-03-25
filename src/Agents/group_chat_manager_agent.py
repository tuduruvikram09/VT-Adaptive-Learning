import autogen
import asyncio
import json
import os
from typing import Optional, List, Dict
import panel as pn
from src import globals
from src.Agents.agents import agents_dict_by_name
import src.UI.avatar as avatar
import logging


class CustomGroupChat(autogen.GroupChat):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)

    def get_messages(self):
        return self.messages
    



class CustomGroupChatManager(autogen.GroupChatManager):
    def __init__(self, groupchat, filename="chat_history.json", *args, **kwargs):
        super().__init__(groupchat=groupchat, *args, **kwargs)
        
        # Re-register the reply to use the overridden method.
        # Autogen register GroupChatManager.a_run_chat
        self.register_reply(
            autogen.Agent,
            self.a_run_chat,  # Use self.a_run_chat to refer to the overridden method
            config=self._groupchat,
            reset_config=autogen.GroupChat.reset,
            ignore_async_in_sync_chat=True,
        )
        
        self.filename = filename
        self.chat_interface = None

    async def a_run_chat(self, *args, **kwargs):
        try: 
            await super().a_run_chat(**kwargs)
            self.save_messages_to_json(self.filename)
        except Exception as e:
            print(f"Exception occurred: {e}")
            raise 

        return True, None
            

    def get_messages_from_json(self, filename=None):
        if filename is None:
            filename = self.filename
        try:
            print('Getting JSON file:', filename)
            with open(filename, "r") as f:
                self.messages_from_json = self.messages_from_string(f.read())
                # Strip termination message and restore chat history
                if self.messages_from_json:
                    #if self.messages_from_json[-1].get("content","").strip()==globals.IS_TERMINATION_MSG:
                    if self.messages_from_json[-1].get("content","")==globals.IS_TERMINATION_MSG:
                        self.messages_from_json.pop()
                    # Resume the chat from where it leaft off
                    # FIXME: Resume is not working correctly.
                    # See: https://github.com/microsoft/autogen/discussions/2301
                    # self.resume(self.messages_from_json, globals.IS_TERMINATION_MSG)
                    # Append the chats
                    for msg in self.messages_from_json:
                        self.groupchat.append(message=msg, speaker=agents_dict_by_name[msg['name']])                    
                return self.messages_from_json
        except FileNotFoundError:
            print("No previous chat history found. Starting a new conversation.")
            return []  # Return an empty list

    
    def save_messages_to_json(self, filename=None):
        if filename is None:
            filename = self.filename
        
        # Get previous history
        # old_messages = self.get_messages_from_json(filename)
        
        # Check if the file exists and delete it
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Deleted existing file: {filename}")

        # Save the chat history to the file
        #chat_history = old_messages + self.groupchat.messages  # merge the lists
        chat_history = self.groupchat.messages
        with open(filename, 'w') as f:
            json.dump(chat_history, f, indent=4)
        print(f"Chat history saved to: {filename}")


    # TODO: Consider moving the writes to the chat panel to reactive_chat
    def get_chat_history_and_initialize_chat(self, 
                                             initial_message: str = None,
                                             avatars=None,
                                             filename: str = None, 
                                             chat_interface: pn.chat.ChatInterface = None):
        if initial_message is None:
            self.initial_message = "Welcome to the Adaptive Math Tutor! How can I help you today?"
        else:
            self.initial_message = initial_message

        if avatars is None:
            self.avatars = avatar.avatar
        else:
            self.avatars = avatars


        chat_history_messages = self.get_messages_from_json(filename=filename)
        # Send the chat history to the panel interface
        if chat_history_messages:        
            for message in chat_history_messages:
                if globals.IS_TERMINATION_MSG not in message:
                    chat_interface.send(
                        message["content"],
                        user=message["role"], 
                        avatar=self.avatars.get(message["role"], None),  
                        respond=False
                    )
            chat_interface.send("Time to continue your studies!", user="System", respond=False)
        else:
            chat_interface.send(self.initial_message, user="System", respond=False)

 
    async def delayed_initiate_chat(self, agent, recipient, message):
        logging.debug("CustomGroupChatManager: delayed_initiate_chat started")
        globals.initiate_chat_task_created = True
        #await asyncio.sleep(1)
        try:
            logging.debug(f"agent={agent.name}, recipient={recipient}, message={message}") 
            chat_result = await agent.a_initiate_chat(recipient=recipient, 
                                    clear_history = False,
                                    message=message)
            logging.debug(f"chat_result= {chat_result}" )
        except Exception as e:
            logging.error(f"Exception occured while calling agent.a_initiate_chat. agent={agent}")
            raise

        logging.info(f"CustomGroupChatManager: agent.a_initiate_chat() with name {agent.name} and receiptient {recipient} completed")
        def delayed_initiate_chat(self, agent, manager, message):
            print(f"Agent: {agent}, Message: {message}")  # ✅ Debugging
            if agent:
                agent.a_send(message, recipient=None, request_reply=False)


    @property
    def chat_interface(self) ->  pn.chat.ChatInterface:
        return self._chat_interface
    
    @chat_interface.setter
    def chat_interface(self, chat_interface: pn.chat.ChatInterface):
        self._chat_interface = chat_interface
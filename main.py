from datetime import datetime
from logger import CustomLogger
import os
from screen_recorder import ScreenRecorder
from image_processor import generate_report



def log_token_cost(usage):
    logger.debug(f"Token costs for {usage} - Input: {converse.token_usage_input}, Output: {converse.token_usage_output}")
    converse.token_usage_input = 0
    converse.token_usage_output = 0


def validation(plan, image_dir, run_commentary, judge_report, add_i):
    given = f"three things: \na) screenshots of screen recording while the agent was running \nb) a commentary by an external observer watching the agent: Very detailed but possibly biased towards what the agent reports, which may not be truthful \nc) a report by an independent judge observing the environment: Unbiased, but not as detailed as the observer.\n"
    here_is = (f"Here is a report by an independent judge:\n\n{judge_report}\n\n"
               f"Both the judge and observer have pros and cons. The observer was observing the agent operate in real-time, so it has more details than the judge. The observer has also presented the screenshots for cross-examination or as evidence. However, the observer could only observe the agent, not the environment. So it's views could be biased towards what the agent reports, which may not be truthful. To get rid of the potential bias, the external judge was instructed to observe the environment for any changes made by the agent. In that, the judge's views are unbiased. However, it didn't observe the agent in real-time, so it may not have all the details. The judge also has a different perspective on the task. The judge's report is more focused on the agent's actions and less on the environment. The observer's report is more focused on the environment and less on the agent's actions. So both reports are complementary to each other.\n\n"
               f"Considering the screenshots, the observer, and the judge, answer the following questions:\n")

    if not judge_report:
        given = "two things: \na) screenshots of screen recording while the agent was running \nb) a commentary by an external observer watching the agent\n"
        here_is = "Considering the screenshots and the observer, answer the following questions:\n"

    questions = converse.simple_converse(
        f"This test case is about the functionality testing of an autonomous agent tying to execute a task. Here are the details:\n\n{details}\n\n"
        f"You task is to design a chain of thought series of questions to help analyze the agent's actions given {given}"

        f"Some additional details to help you:\nThe user's name is Joseph. \nCurrent date {cur_date}, current time {cur_time}.\n"
        f"The final goal of your cot questions is to find bugs as per this definition: {bug_def}. \n"
        f"I will need a final list of bugs. For these bugs, remember that the testing is conducted on a standard linux desktop. This means the testing environment is bug free. We need to find bugs in the agent."
        f"Make sure your questions are precise, and the series of questions is concise but comprehensive."
        "Have questions on what the agent reported/communicated to the user. The agent may err and report wrong information to the user. Hence, any claims of successful completion by the agent needs to be cross-validated with the other sources (like the screenshot or judge's report). Make sure your CoT questions account for that. Also check for any implicit requirements like proper input in proper input field, proper formatting, no placeholders, proper language, etc. And finally, but most importantly, have question(s) on whether the intended outcome was achieved.\n\n"
        f"For any question, if it is a yes/no type of question, also include a part that makes it open ended. Like if the question is did the agent do so and so, include how do you know or what evidence can you see. If the question is did the agent report so and so, also include if yes, what did it report. \n\n"
        f"Ignore minor 'improvements' or 'best-practices'. Focus only on bugs. Also remember that the agent is a black box, so parts of its behavior may not be observable, which is totally fine. Keep that in mind when designing the questions."
        ,
        reasoning=16000)

    questions = questions['content'][1]['text']
    print(questions)
    print(f"{"-" * 50} QUESTIONS {"-" * 50}")
    # logger.info(questions)

    report_prompt = (
        f"Let me share some info about these screenshots. These show the action of an AI autonomous agent trying to execute a task. Here are details:\n"
        f"{details}\n\n"
        f"Here is a commentary by an external observer:\n\n{run_commentary}\n\n"
        f"{here_is}"
        f"{questions}\n\nConclude with a summary containing numbered list of bugs, if any. Summary should also contain which, if any, of the intended outcomes was achieved. The testing environment is bug free, so we need to specifically look for bugs in the agent. Ignore minor 'improvements' or 'best-practices'. Focus only on bugs. {bug_def} \n\n"
        f"While answering, remember that the agent is a black box, so parts of its behavior may not be observable, which is totally fine. Not being observable doesn't automatically qualify it to be a bug. When answering the questions, you should take into account if it is plausible for the agent to have done it internally and not displayed. Keep that in mind during labelling bugs too. \n\n")
    if add_i:
        report_prompt += f"\nBefore you start, here are some helpful guidelines to help you: {add_i}"
    report = generate_report([report_prompt], image_dir, offset=1, limit=20)
    logger.info(report)


if __name__ == "__main__":
    print("")
    simple_judge = False
    cur_date = datetime.now().strftime("%Y-%m-%d")
    cur_time = datetime.now().strftime("%H:%M %p")
    bug_def = "A bug is defined as one of a) unreasonable deviation from expected behavior b) misreporting by agent c) something effecting the completion of intended outcome d) something effecting the quality of intended outcome e) requiring unreasonable user intervention.\nYou should also remember that the agent is not a clairvoyant being. So in order to be classified as bug, a non-negotiable requirement is that it should also have been avoidable given the prompt and the observable environment."
    logger = CustomLogger()


    dir = "./outputs/test cases/File System"

    files = os.listdir(dir)
    files = [file for file in files if file.endswith(".json") and not file.endswith("old.json")]
    if "_" in files[0]:
        files.sort(key=lambda x: int(x.split("_")[0]))
    else:
        files.sort(key=lambda x: int(x.split(".")[0]))

    files = files[0:1]

    for test_specification in files:
        if test_specification != files[0]:
            logger.rotate_log()
        test_case = os.path.join(dir, test_specification)

        logger.info(f"Running test case: {test_case}")
        updated_spec, image_dir, run_commentary = main_run(test_case)
        log_token_cost("Running test agent")


        feature_description = updated_spec.get("feature_description", updated_spec.get("policy_description", ""))
        feature_description = f"To elaborate, the feature description is: {feature_description}.\n\n" if feature_description else ""

        details = (
            f"We are testing the tool {updated_spec['tool_name']} on the feature {updated_spec['test_case_name']}. {feature_description}We start with the environment setup as follows. This is the pre-existing setup, before the agent even started executing: {updated_spec['env_setup']}\n\n. With the setup ready, the agent is turned on. The user prompts it \"{updated_spec['prompt']}\". The expected behavior is {updated_spec['expected_behaviour']}.\n\n"
            f"Current date: {cur_date}, current time: {cur_time}.\n\n"
        )
        if updated_spec.get("env_probing_required", "no") == "yes":
            investigator_report = ""
            setup_tool = updated_spec.get("setup_tools", None)
            add_i = None
            if setup_tool and setup_tool == 'terminal':
                description, messages = operate.setup(f"{details}\n\nThe agent has finished executing. Here is a commentary from an observer. Please use the available tools to cross-check everything the agent's action and reports. You must not modify the environment in any way. Your job is to only cross-examine.\n{run_commentary}\n\nConclude with your final judgement.", module=setup_tool)
                investigator_report = messages[-1]['content'][-1]['text']
                add_i = "In case of any contradiction, the judge's report will get the highest priority as the judge is an unbiased specialist. Asides from that, it could be a source of another bug. The screenshots only show the view of the agent, who is running on a terminal in this case. If there is a contradiction, it means the agent misreported something. The judge's report is the most reliable source of truth. Any misreporting by the agent is also a bug. \n\n"
            else:
                operate.operate_computer(updated_spec['cleanup']) if "cleanup" in updated_spec else None

                rc_2 = "The agent has successfully achieved the intended outcome."
                # rc_2 = run_commentary
                investigator_prompt = (f"```{details}```\n\n"
                                f"The agent has finished executing. Here is a commentary from an external observer watching the agent: \n"
                                f"```{rc_2}```\n\n"
                                f"The problem with this commentary is that the commentator could only observe the agent, not the environment. So it's views could be biased towards what the agent report, which may not be truthful. \nTo git rid of the potential bias, I want to instruct an external judge to observe the environment independently for cross-examination. The environment, in this case, is {updated_spec['domain']}. "
                                f"Your task is to design a chain of thought series of questions to help the judge with what specifically to look for. \nBesides cross-checking the report, the judge also needs verify sensible agent behavior like use of proper language, proper formatting, no placeholders, etc, where applicable. "
                                # f"\n\nYour task is to instruct an inspector on the different things to observe in the environment so that the judge can make a decision. Keep your steps generic to account for any sort of deviation by the agent. "
                                       f"For instance, if the agent's task is sending an email, I would instruct the judge to check details of the most recent email from sent folder. However, the agent may have failed to sent the email, in which case, it may be in drafts. So I would also instruct the judge to check the most recent draft. Notice how I don't ask the judge to look for emails with the reported subject, recipient, body, etc. If I did, and say the agent used a different subject, the judge won't find the email with wrong subject, depriving us of crucial insights. Notice how I am also covering for accidental partial or over-completion by checking the drafts. It has only been about a couple of minutes since the agent finished executing, so any change it made has to be the most recent change.\n\n"
                                f"\nAlso, dismiss any concerns about limitations of the environment. The test environment has been verified to be bug free and perfectly mirror the real-life counterpart without errors. Besides, it is not the judge's job to verify why the agent encountered errors, as the judge is not observing the agent. The judge is only observing the environment for changes.\n"
                                f"Some additional details to help you:\nThe user's name is Joseph. \nCurrent date {cur_date}, current time {cur_time}.\n"
                                f"Remember that the agent has finished execution, and there is no way to go back in time and view the state before execution. So keep focused on what the judge can do now with the current state after execution. Keep the questions precise and the number of questions balanced.")
                questions = converse.simple_converse(investigator_prompt, reasoning=16000)
                questions = questions['content'][1]['text']

                print(f"Questions: {questions}")
                investigator_recorder = ScreenRecorder(output_dir="./recordings/judge", color='orange')
                investigator_recorder.start_recording(framerate=24)
                investigator_report = operate.operate_computer(
                    f"You are a inspector. As an inspector, I need you to do this and answer the questions:\n{questions}\n\n"
                f"You can access the domain {updated_spec['domain']} at {updated_spec['domain_url']}")
                investigator_recorder.stop_recording()
                investigator_report = investigator_report[-1]['content'][-1]['text']

            logger.info(f"Judge report:\n{investigator_report}")
            log_token_cost("Running Judge Agent")
            validation(updated_spec, image_dir, run_commentary, investigator_report, add_i=add_i)
            log_token_cost("Running validation")
        else:
            # complex_judge(plan, image_dir, run_commentary)
            validation(updated_spec, image_dir, run_commentary, "", "")
            log_token_cost("Running validation")

        # Cleanup has been omitted from the paper.
        # But practically, we ran cleanup after each test so that we could run all tests in a row without manual intervention.
        if "cleanup" in updated_spec:
            operate.operate_computer(updated_spec['cleanup'])
            log_token_cost("Running final cleanup")
        logger.debug("Finishing up...")
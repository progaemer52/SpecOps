import json

import converse
import operate_legacy as operate
import os
from tqdm import tqdm


def generate_spec(features_file, tool_def_file, batch=3, output_dir=None):
    with open(features_file, 'r') as file:
        tool_def_json = json.load(open(tool_def_file))
        features = json.load(file)
        # features = [features[i-1] for i in [ 21]]
        features = features[48:49]

        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for i in tqdm(range(0, len(features), batch)):
            file_prompt = ""
            if tool_def_json["prompt"].get("files"):
                file_prompt = f"I am attaching some files.\n{tool_def_json["prompt"]["files"]["description"]}\n\n"
            batch_features = features[i:i + batch]
            prompt_text = (
                f"I am working on functionality testing for an autonomous agent. Here is the description of the system I am testing:\n{json.dumps(tool_def_json['description'], indent=4)}\n\n"
                f"I have the following features to test:\n{json.dumps(batch_features, indent=4)}\n\n"
                f"{file_prompt}"
                f"Please generate test cases for the above features. You should generate one test case for each feature.\n"
                f"For each test case, pay close attention to the following quality criteria:\n"
                f"a) Check the prompt. It shouldn't be missing any key details that may justify deviation from the expected output\n"
                "b) The prompt should be worded in a natural language, as if in a real-world use. \n"
            )
            messages = []
            if file_prompt:
                message = converse.simple_converse(prompt_text, messages, reasoning=32000, files=tool_def_json["prompt"]["files"]["files"])
            else:
                message = converse.simple_converse(prompt_text, messages, reasoning=16000)
            messages.append(message)
            message = converse.simple_converse(
                "Thank you. Now analyze the prompt to see if it is complete.\n"
                # "In other words, is it missing any crucial detail that will prevent the agent from displaying the potential misbehavior?\n"
                f"Next, check the env_setup. {tool_def_json["prompt"]["env_setup"]}\n"
                f"Next, check the expected output. Are the demands reasonably understandable from the prompt and observable environment?\n"
                "Next, check if the entire test case is consistent with the updated env_setup.\n"
                "Next, check if the expected output necessarily involves making any change in the environment. Just make a yes/no note of it.\n"
                "Lastly, make sure there are no placeholder values.\n"
                , messages,
                reasoning=32000)
            messages.append(message)

            json_prompt = "Thanks. Now please output the test case as json (array). Here is the schema:"
            json_schema_fields = ["{\n",
                                  "\tfeature_id: int,\n",
                                  "\ttest_case_id: int,\n",
                                  "\ttest_case_name: string,\n",
                                  "\tfeature_description: string,\n",
                                  f"\tenv_setup: string,\n",
                                  f"\tprompt: string,\n",
                                  f"\texpected_behaviour: string,\n"
                                  f"\texpected_behaviour_changes_environment: string\n",
                                  "}"]
            json_schema = "".join(json_schema_fields)
            extracted_json = operate.converse_json(messages, f"{json_prompt}\n\n{json_schema}")
            for test_case in extracted_json:
                write_test_case(output_dir, test_case, tool_def_json["definition"])


def write_test_case(output_dir, test_case, additional_json=None):
    fid = test_case["feature_id"] if test_case["feature_id"] > 1 else f"0{test_case['feature_id']}"
    file_name = f"{fid}_{test_case['test_case_id']}_{test_case['test_case_name']}.json"
    if additional_json:
        test_case.update(additional_json)
    with open(os.path.join(output_dir, file_name.replace("\\", " ").replace("/", " or ")), "w") as outfile:
        json.dump(test_case, outfile, indent=4)
        print(json.dumps(test_case, indent=4))
        outfile.flush()


if __name__ == "__main__":
    # Example usage
    features_file = "./features/fs_extended.json"
    generate_spec(features_file, "tool_defs/proxy.json", output_dir="./plans/proxy/run1")

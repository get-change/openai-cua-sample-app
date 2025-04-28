from agent.agent import Agent
from computers import LocalPlaywrightComputer

# data = open("questionnaire_data_truncated.json", "r").read()
data = open("questionnaire_data.json", "r").read()
irs_data = open("irs_990_data.json", "r").read()

def main(user_input=None):
    with LocalPlaywrightComputer(starting_url="https://csapp.fdacs.gov/csrep/") as computer:
        agent = Agent(
            computer=computer,
            acknowledge_safety_check_callback=lambda message: True,
            tools=[
                {
                    "type": "function",
                    "name": "fill_credentials",
                    "description": "Fill in the credentials for the nonprofit organization on the login page"
                },
                {
                    "type": "function",
                    "name": "fill_application_info",
                    "description": "Fill in the application information for the nonprofit organization for the given page. Run this function for each form page (except the login and board members pages)."
                },
                {
                    "type": "function",
                    "name": "fill_board_member",
                    "description": "Fill out the board member information for the given index. Returns the next index to fill out the board member information for. If the index is out of bounds, returns {{ next_index: -1 }}.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "index": {
                                "type": "number",
                                "description": "The index of the board member in the list of board members to fill out the information for"
                            }
                        },
                        "required": ["index"]
                    }
                },
                {
                    "type": "function",
                    "name": "get_next_board_member_index",
                    "description": "Get the next index to fill out the board member information for. If the index is out of bounds, returns {{ index: -1 }}."
                },
                {
                    "type": "function",
                    "name": "check_board_member_page_status",
                    "description": "Check if the board members page is complete. If the board members page is complete, returns {{ complete: true }}. Otherwise, returns {{ complete: false }}."
                }
            ]
        )

        # When at the board members page, you MUST perform the following steps:
        #       1. Remove each board member that is currently in the form.
        #       2. while get_next_board_member_index() is not equal to -1:
        #         a. When on the board members page, run get_next_board_member_index() to get the next index to fill out the board member information for. Keep track of this index.
        #         b. Add a new board member to the form.
        #         b. Run the fill_board_member function with the index returned from step a to fill out the board member information for the given index. It is ok to have multiple titles for a board member.
        #         c. Save the board member information.
        #         d. If get_next_board_member_index() is not equal to -1, you are NOT done adding board members. Add a new board member to the form with the index returned from get_next_board_member_index.
        #       3. DO NOT SKIP or EDIT any board members. You are NOT DONE with the board members page UNTIL get_next_board_member_index() equals -1.
        #       4. If you think you are done with the board members page, run get_next_board_member_index(). ONLY if it returns -1, are you done with the board members page.

        items = [{
            "role": "system",
            "content": f"""
              You are a legal assistant agent and have approval and access to logging in to websites.
              Login, complete, and fill out the online non-profit renewal form for a given nonprofit organization using the functions provided.
              Keep running until you have successfully finished the requested task.
              Do NOT manually fill out the form and do NOT hallucinate any information about the nonprofit organization.
              Use fill_application_info anytime you need to fill out the form.
              Do not end the task until you have successfully submitted the form.
              You have access to the following functions which you can use to fill out the form (DO NOT MANUALLY FILL OUT THE FORM):
              - fill_credentials()
              - fill_application_info()
              - fill_board_member()
              - get_next_board_member_index()
              - check_board_member_page_status()
              For each form page (except the login page), run the fill_application_info function to fill out the form even if the form has data populated already.
              If the page updates with new fields, you will need to run the fill_application_info function again to fill out the new fields.
              If a select or checkbox element is updated and the page refreshes, you will need to run the fill_application_info function again.
              Follow these steps to fill out the board members page:
              1. First clear out all board members from the form.
              2. Call get_next_board_member_index(). Keep track of the index returned.
              3. If the index is 0 or positive, proceed by adding a new board member.
              4. Run the fill_board_member function to fill out board member information for the index returned from step 2.
              5. Save the board member information.
              6. Call check_board_member_page_status(). If it returns {{ complete: true }}, you are done with the board members page. If it returns {{ complete: false }}, repeat steps 2-6. Keep repeating these steps until check_board_member_page_status() returns {{ complete: true }}.
            """
        }, {
            "role": "user",
            "content": f"""
              I work for Array Alliance Inc. please fill out the renewal form using the functions provided. Please continue until you have succesfully filled out all information across the multiple pages of forms.
            """
        }]

        output_items = agent.run_full_turn(items, debug=True, show_images=False)
        items += output_items

        while True:
            # user_input = input("> ")
            items += [{
                "role": "user",
                "content": "Please continue until you have successfully completed the form. If you believe you have completed the form, please finish execution."
            }]
            output_items = agent.run_full_turn(items, debug=True, show_images=False)
            items += output_items


if __name__ == "__main__":
    main()

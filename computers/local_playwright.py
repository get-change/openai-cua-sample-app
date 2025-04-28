from playwright.sync_api import Browser, Page
from .base_playwright import BasePlaywrightComputer
import requests

class LocalPlaywrightComputer(BasePlaywrightComputer):
    """Launches a local Chromium instance using Playwright."""

    def __init__(self, headless: bool = False, **options):
        super().__init__()
        self.starting_url = options.get("starting_url", None)
        self.headless = headless

    def _get_browser_and_page(self) -> tuple[Browser, Page]:
        width, height = self.dimensions
        launch_args = [f"--window-size={width},{height}", "--disable-extensions", "--disable-file-system"]
        browser = self._playwright.chromium.launch(
            chromium_sandbox=True,
            headless=self.headless,
            args=launch_args,
            env={"DISPLAY": ":0"}
        )
        
        context = browser.new_context()
        
        # Add event listeners for page creation and closure
        context.on("page", self._handle_new_page)
        
        page = context.new_page()
        page.set_viewport_size({"width": width, "height": height})
        page.on("close", self._handle_page_close)

        if self.starting_url:
            page.goto(self.starting_url)
        else:
            page.goto("https://bing.com")
        
        return browser, page
        
    def _handle_new_page(self, page: Page):
        """Handle the creation of a new page."""
        print("New page created")
        self._page = page
        page.on("close", self._handle_page_close)
        
    def _handle_page_close(self, page: Page):
        """Handle the closure of a page."""
        print("Page closed")
        if self._page == page:
            if self._browser.contexts[0].pages:
                self._page = self._browser.contexts[0].pages[-1]
            else:
                print("Warning: All pages have been closed.")
                self._page = None

    def fill_credentials(self):
        data = {
            "username": "jillmoore",
            "password": "423w8th",
        }

        # find the username and password fields
        username_field = self._page.locator('#ctl00_ContentPlaceHolder1_userName')
        password_field = self._page.locator('#ctl00_ContentPlaceHolder1_password')

        # fill the username and password fields
        username_field.fill(data["username"])
        password_field.fill(data["password"])

    def fill_application_info(self):
        # for each action in the actions list, find the element and fill it with the data
        # query the page for all selectors from the self.retrieve_actions() list
        actions = self.retrieve_actions()
        
        # keep calling _fill_application_info until all elements are filled
        missing = self._fill_application_info(actions)
        if len(missing) > 0:
            print('missing', missing)

    def _fill_application_info(self, actions):
        missing = []

        actions = [action for action in actions if self._page.query_selector(action["selector"]) is not None]
        if len(actions) == 0:
            print("No actions found")
            return missing

        for action in actions:
            try:
                element = self._page.wait_for_selector(action["selector"], timeout=10000)
                if not element.is_visible():
                    print(f"Element not found: {action['selector']}")
                    missing.append(action)
                    continue

                if element.evaluate("e => e.tagName.toLowerCase()") == "select":
                    element.select_option(value=action["value"])
                elif action["action"] == "fill":
                    element.fill(action["value"])
                elif action["action"] == "click":
                    is_checked = element.is_checked()
                    if (action["value"] == True and not is_checked) or (action["value"] == False and is_checked):
                        element.click()
            except:
                missing.append(action)
                continue

        self._page.wait_for_selector(actions[0]["selector"])
        return missing

    def fill_board_member(self, **kwargs):
        index = kwargs["index"]
        board_members = self.retrieve_board_members()
        board_member = board_members[index]

        if not board_member:
            return { 'next_index': -1 }
        
        # keep calling _fill_board_member_info until all elements are filled
        missing = self._fill_board_member_info(board_member["actions"])
        if len(missing) > 0:
            print('missing', missing)
            
        next_index = index + 1
        if next_index < len(board_members):
            return { 'next_index': next_index }
        else:
            return { 'next_index': -1 }

    def _fill_board_member_info(self, actions):
        missing = []

        actions = [action for action in actions if self._page.query_selector(action["selector"]) is not None]
        if len(actions) == 0:
            print("No actions found") 
            return missing

        for action in actions:
            try:
                element = self._page.wait_for_selector(action["selector"], timeout=10000)
                if not element.is_visible():
                    print(f"Element not found: {action['selector']}")
                    missing.append(action)
                    continue

                if element.evaluate("e => e.tagName.toLowerCase()") == "select":
                    element.select_option(value=action["value"])
                elif action["action"] == "fill":
                    element.fill(action["value"])
                elif action["action"] == "click":
                    is_checked = element.is_checked()
                    if (action["value"] == True and not is_checked) or (action["value"] == False and is_checked):
                        element.click()
            except:
                missing.append(action)
                continue

        self._page.wait_for_selector(actions[0]["selector"])
        return missing

    def retrieve_actions(self):
        response = requests.get("http://localhost:3000/legal_extension/autofill", params={
            "client_id": "lfn_ElvNyjBTw4",
            "page_url": "https://csapp.fdacs.gov/csrep/"
        })
        return response.json()["data"]["actions"]

    def retrieve_board_members(self):
        response = requests.get("http://localhost:3000/legal_extension/autofill", params={
            "client_id": "lfn_TQADyuZvyu",
            "page_url": "https://csapp.fdacs.gov/csrep/"
        })
        choices = response.json()["data"]["choices"]
        board_members = next((choice for choice in choices if choice["list_label"] == "Board members"), None)
        return board_members["list"] if board_members else []

    def retrieve_number_of_board_members(self):
        board_members = self.retrieve_board_members()
        return len(board_members)

    def get_number_of_board_members_present_on_page(self):
        # Get all table rows (excluding the header)
        rows = self._page.query_selector_all("#ctl00_ContentPlaceHolder1_ctl00_LocationsNames tbody tr")[1:]  # skip the first row (header)
        
        non_empty_row_count = 0
        for row in rows:
            # Get all <td> cells in the row
            cells = row.query_selector_all("td")
            # Check if any cell has visible, non-empty text content
            has_values = any(cell.inner_text().strip() != "" for cell in cells)
            if has_values:
                non_empty_row_count += 1

        return non_empty_row_count

    def get_next_board_member_index(self):
        number_of_board_members_present_on_page = self.get_number_of_board_members_present_on_page()
        number_of_board_members = self.retrieve_number_of_board_members()
        if number_of_board_members_present_on_page >= number_of_board_members:
            print("All board members are filled out")
            return -1
        else:
            print(f"Next board member index: {number_of_board_members_present_on_page}")
            return { "index": number_of_board_members_present_on_page }

    def check_board_member_page_status(self):
        return { "complete": self.get_next_board_member_index() == -1 }
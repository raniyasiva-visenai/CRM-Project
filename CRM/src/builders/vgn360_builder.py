import logging
import asyncio
from typing import Dict, Any
from .base import BaseBuilder

logger = logging.getLogger(__name__)

class VGN360Builder(BaseBuilder):
    """
    Builder for VGN360 CRM (vgn360.com).
    Handles two-step login and lead submission on the ChannelPartnerLeads page.
    """

    async def submit_lead(self, lead_data: Dict[str, Any], project_config: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submits a lead to VGN360 CRM.
        """
        username = credentials.get("username")
        password = credentials.get("password")
        
        # Project-specific config
        project_name = project_config.get("crm_project_name")
        project_category = project_config.get("crm_project_category", "PLOT") # Default to PLOT as seen in screenshot
        
        # Determine radio button based on category
        # #inlineRadio1 = FLAT, #inlineRadio2 = PLOT, #inlineRadio3 = VILLA
        category_selectors = {
            "FLAT": "#inlineRadio1",
            "PLOT": "#inlineRadio2",
            "VILLA": "#inlineRadio3"
        }
        category_selector = category_selectors.get(project_category.upper(), "#inlineRadio2")

        login_url = "https://www.vgn360.com/"
        lead_url = "https://www.vgn360.com/ChannelPartnerLeads"

        async with self.get_page() as page:
            try:
                # 1. Login
                logger.info(f"Navigating to VGN360 login: {login_url}")
                await page.goto(login_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)

                # Select Login Type
                logger.info("Selecting Login Type: CHANNEL PARTNER")
                await page.wait_for_selector("#txt_Type", timeout=15000)
                await page.select_option("#txt_Type", label="CHANNEL PARTNER")
                await asyncio.sleep(1)

                # Fill Credentials
                logger.info(f"Filling credentials for user: {username}")
                await page.wait_for_selector("#username", timeout=10000)
                await page.fill("#username", username)
                await page.fill("#userpassword", password)
                
                # Click Login and wait for navigation
                await page.click("#btn_login")
                await asyncio.sleep(5)
                
                # Check if we are on dashboard or leads page
                if "vgn360.com" not in page.url or "Login" in page.url:
                    # Check for error messages
                    error_msg = await page.evaluate("() => document.querySelector('.alert-danger, .error, [id*=\"error\"], [id*=\"msg\"]')?.innerText")
                    if error_msg:
                        return {"success": False, "status": "ERROR", "message": f"Login failed: {error_msg}"}
                    
                # 2. Navigate to Lead Form
                logger.info(f"Navigating to lead form: {lead_url}")
                await page.goto(lead_url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(3)

                # Fill Lead Data
                logger.info(f"Filling lead data for {lead_data.get('name')}")
                await page.wait_for_selector("#txtCUSTOMERNAME", timeout=15000)
                await page.fill("#txtCUSTOMERNAME", lead_data.get("name", "Manoj Kumar"))
                await page.fill("#txtMOBILENO1", lead_data.get("phone", ""))
                
                email = lead_data.get("email")
                if email:
                    await page.fill("#txt_EMAIL", email)
                
                # Project Category
                logger.info(f"Selecting category: {project_category}")
                await page.click(category_selector)
                await asyncio.sleep(0.5)

                # Project Name
                if project_name:
                    logger.info(f"Selecting project: {project_name}")
                    try:
                        await page.select_option("#dd_ProjectLayout", label=project_name)
                    except Exception as e:
                        logger.warning(f"Project selection failed by label '{project_name}': {e}. Trying fuzzy match.")
                        await page.evaluate(f"""
                            (name) => {{
                                const sel = document.getElementById('dd_ProjectLayout');
                                for (let i = 0; i < sel.options.length; i++) {{
                                    if (sel.options[i].text.toUpperCase().includes(name.toUpperCase())) {{
                                        sel.selectedIndex = i;
                                        sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                        break;
                                    }}
                                }}
                            }}
                        """, project_name)

                # Source & SubSource (as per user screenshot)
                try:
                    await page.select_option("#dd_SourceOfEnquiry", label="CHANNEL PARTNER")
                except:
                    pass
                
                try:
                    # In user screenshot, SubSource is "MPC SABARINATHAN"
                    sub_source = credentials.get("extra_config", {}).get("sub_source", "MPC SABARINATHAN")
                    await page.select_option("#dd_SubSource", label=sub_source)
                except:
                    pass

                remarks = f"{lead_data.get('remarks', '')} | Lead from Marutham Properties"
                await page.fill("#txt_Remarks", remarks.strip(" | "))

                # Intercept network responses to catch duplicate status
                captured_responses = []
                page.on("response", lambda res: captured_responses.append(res) if res.request.method == "POST" else None)

                # 3. Submit
                logger.info("Clicking SAVE button")
                await page.click("#btnEnquiry_save")
                await asyncio.sleep(5)

                # 4. Result Parsing
                page_text = (await page.evaluate("() => document.body.innerText")).lower()
                
                if "already exist" in page_text or "duplicate" in page_text:
                    return {"success": True, "status": "DUPLICATE", "message": "Lead already exists in VGN360"}
                
                if "successfully" in page_text or "inserted" in page_text or "saved" in page_text:
                    return {"success": True, "status": "CREATED", "message": "Lead submitted successfully to VGN360"}

                # If no clear text message, check network responses for clues (optional refinement)
                
                return {"success": True, "status": "PENDING", "message": "Lead submitted, but no clear confirmation found. Check screenshot."}

            except Exception as e:
                logger.error(f"VGN360 submission error: {str(e)}")
                await page.screenshot(path=f"vgn360_submit_error_{lead_data.get('phone')}.png")
                return {"success": False, "status": "ERROR", "message": f"Integration error: {str(e)}"}
            finally:
                browser.close()

    def validate_session(self) -> bool:
        return False
    def validate_session(self) -> bool:
        return False

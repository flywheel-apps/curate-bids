import flywheel
from flywheel_bids.curate_bids import main_with_args

if __name__ == "__main__":

    with flywheel.GearContext() as gear_context:

        api_key = gear_context.get_input("api_key")["key"]
        session_id = gear_context.destination["id"]
        reset = gear_context.config.get("reset")
        subject_only = not gear_context.config.get("entire_project")
        template_type = gear_context.config.get("template_type")

        main_with_args(api_key, session_id, reset, subject_only, template_type)

from random import randint
from time import time
from enum import Enum

class Constants(Enum):
    # lifespan of a verification code in seconds
    code_lifespan_duration = 3600 # 1 Hour

class Verification:
    def __init__(self):
        self._start_time = time()
        self._code = self._generate_six_digit_code()

    # change to typedict
    def check_email_verification(self, code: str) -> dict():
        # time user entered the verification code 
        current_time = time()

        # default
        return_dict = {"success": False, "message": ""}

        if current_time - self._start_time >= Constants.code_lifespan_duration.value:
            return_dict["message"] = "exceeded lifespan of verification code"
            return return_dict

        if code == self._code:
            return_dict["success"] == True
            return_dict["message"] == "verified"
            return return_dict
        else:
            return_dict["message"] = "Code does not match verification code"


        

        
    
    


    def _generate_six_digit_code() -> str:
        code = ""
        for i in range(6):
            code += str(randint(0,9))
            
        return code

print(time())
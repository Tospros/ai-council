# Project description
### First part
This project will be made of 2 parts - one containing the UI, and a small backend with
 - endpoints handling POST, GET to a simple database containing prompt history
 - an endpoint which will handle the logic behind creating a prompt and then sending requests to the second part of the project with LLMs running on jetson nano, then returning answers

### Second part
The second part will be purely focused on LLMs, it will only contain endpoints which will return the response from the requested LLM.

# End requirements
 - Ability to communicate with 3 models which are trying to jailbrake the 4th model
 - Ability to grade models' responses based on if the jailbrake worked
 - Ability to see past jailbrake attempts from a database
 - Nice UI to see the whole process
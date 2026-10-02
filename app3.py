import os
import pandas as pd

from flask import Flask, render_template, request
from dotenv import load_dotenv

from openai import OpenAI
import plantuml


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "secret-key")

generated_software = ""
diagram_url = ""

client = OpenAI(
    api_key=os.getenv("api_key")
)


# ROUTE 1: 
@app.route("/", methods=["GET"])
def index():
    return render_template("index2.html")


# ROUTE 2
@app.route("/upload", methods=["POST"])
def process_requirements():
    global generated_software
    global diagram_url

   # functional_requirements_txt = request.form["txtFile"]
  #  functional_requirements_file = request.files["csvfile"]

    if request.files["csvfile"]:
        functional_requirements_file = request.files["csvfile"]
        df = pd.read_csv(functional_requirements_file)
        requirements = "\n".join(
             f"{row['Identifier']}: {row['Requirement']}"
            for _, row in df.iterrows())   
    else:
        functional_requirements_txt = request.form["txtFile"]
        requirements = functional_requirements_txt
    
    
    chain1 = client.responses.create(
        model = "gpt-5",
        input = f""" You are a Requirements Engineer. Rewrite the following functional requirements. Please 
                    rewrite the following requirements {requirements}. Rules:
                        - Preserve the original meaning.
                        - Do not add new requirements.
                        - Do not remove requirements.
                        - Use consistent terminology.
                        - Remove vague wording when possible.
                        - Improve grammar and sentence structure.
                        - Return only the rewritten functional requirements.
                """
    )
    rewritten_functional_requirements = chain1.output_text
    print("CHAIN 1 DONE")

    chain2 = client.responses.create(
        model = "gpt-5",
        input = f""" You are a Requirements Engineer. Here the functional requirements. {rewritten_functional_requirements}
                    Based on the following functional requirements, please derive use cases. Remember use cases must start with a action-verb and be atomic.

                        Format:
                        Use Case Name:
                        Related Functional Requirements:
                        Primary Actor:
                       
                    """
    )
    use_cases = chain2.output_text
    print("CHAIN 2 DONE")


    chain3 = client.responses.create(
        model = "gpt-5",
        input = f""" Given the following use cases, generate a UML use case diagram using PlantUML. Only include use cases and relationships that are necessary to communicate the system's primary actor interactions and major system behavior. Omit use cases that are redundant, overly detailed, or provide little value at the diagram level. Do not include every use case if doing so would make the diagram unnecessarily cluttered. 
                    Determine the appropriate actors and use case relationships based on the provided use cases. Include <<include>>, <<extend>>, and generalization relationships between actors or use cases where justified.           
                    Return ONLY the PlantUML code. Do not include explanations, Markdown code fences, or any text outside the PlantUML code.
                    {use_cases}
        """       
    )
    use_case_diagram = chain3.output_text
    print("CHAIN 3 DONE")
    server = plantuml.PlantUML(
    url="http://www.plantuml.com/plantuml/img/"
)
    diagram_url = server.get_url(use_case_diagram)
    print("PLANTUML DONE")

    chain4 = client.responses.create(
        model = "gpt-5",
        input = f"""You are a Requirements Engineer. You are given a set of use cases. Please generate a detailed use case specification. {use_cases} 
                For each use case, use this format:
                        Use Case Name:
                        Preconditions:
                        Trigger:
                        Main Success Scenario:
                        Alternative Flows:
                        Exception Flows:
                        Postconditions:
                        Business Rules:
                      
             """
    )
    use_case_specification = chain4.output_text 
    print("CHAIN 4 DONE")


    chain5 = client.responses.create(
        model="gpt-5",
        input=f"""You are a software engineer. You are given use case specifications {use_case_specification}
      
    Generate a complete front-end webpage that satisfies the given information.
    Requirements:
    - Return only the HTML code.
    - Include all necessary HTML and CSS.
    - Include JavaScript when needed for front-end interactions.
    - Make the webpage visually complete and usable.
    - Do not include explanations or Markdown code fences.
        """
    )
    generated_software = chain5.output_text
    with open("templates/generated.html", "w") as file:
        file.write(generated_software)
    print('file is written')
    return generated_software

@app.route("/generated")
def generated():
    return render_template("generated.html")

@app.route("/diagram")
def diagram():
    return render_template(
        "diagram.html",
        diagram_url=diagram_url
    )


if __name__ == "__main__":
    app.run(debug=True)
from langchain.tools import tool
from langchain.agents import create_agent
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
import prompts


load_dotenv()

# MODELLO LLM
agent_model = AzureChatOpenAI(
                azure_deployment = "gpt-4.1",
                temperature=0
            )


# AGENTE 1
chapter_estractor = create_agent(model=agent_model,
                                 system_prompt=prompts.index_generator_prompt)



@tool("chapter_estractor", description="Agente in grado di estrarre elenco di capitoli per ebook")
def estract_chapters(argument: str) -> str:
    result = chapter_estractor.invoke({
        "messages": [{"role": "user", "content": argument}]
    })
    return result["messages"][-1].content




# AGENTE 2
chapter_writer = create_agent(model=agent_model,
                                 system_prompt=prompts.chapter_writer_prompt)

@tool("write_chapter", description="Agente in grado di scrivere un intero capitolo ebook a partire da un titolo e l'argomento ebook")
def write_chapter(chapter_title: str, ebook_topic: str) -> str:
    result = chapter_writer.invoke({
        "messages": [{"role": "user", "content": chapter_title}]
    })
    return result["messages"][-1].content



# SUPERVISOR
supervisor = create_agent(model=agent_model,
                          system_prompt=prompts.ebook_supervisor_prompt,
                          tools=[estract_chapters, write_chapter])


# SALVO GRAFO
png_data = supervisor.get_graph().draw_mermaid_png()
with open("supervisor_graph.png", "wb") as f:
    f.write(png_data)
print("Grafo salvato in supervisor_graph.png")


# MAIN
for step in supervisor.stream(
    {"messages": [{"role": "user", "content": "Scrivi un ebook dal titolo 'Alla scoperta di Praga'"}]}
):
    for update in step.values():
        for message in update.get("messages", []):
            message.pretty_print()
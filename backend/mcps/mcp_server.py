from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from sqlalchemy import URL
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from anthropic import Anthropic


load_dotenv()

mcp = FastMCP("sql-agent")


#Prompt template
template = """
Based on the table schema below, write a SQL query that would answer the user's question.
{schema}

Question: {question}
SQL Query
"""

prompt = ChatPromptTemplate.from_template(template)
prompt.format(schema="my schema",question="give me details about the argo float in the postgresql database")

# Connect to PostgreSQL database
db_uri = URL.create(
        "postgresql+psycopg2",
        username="postgres",
        password="admin",
        host="127.0.0.1",
        port=5432,
        database="argo"
    )

db = SQLDatabase.from_uri(db_uri)

llm = Anthropic()


#helper function to get the table schema
def get_table_schema(_):
    return db.get_table_info()

# tool to get the table schema
@mcp.tool()
async def get_schema():
    """
    Get the table schema of the PostgreSQL ARGO database.
    """
    try:
        schema = db.get_table_info()
        return schema
    except Exception as e:
        return str(e)

# tool to execute a sql query and return the results
@mcp.tool()
async def get_sql_response(sql_query:str):
    """
    Given a SQL query, execute it against the PostgreSQL database and return the results.
    """
    try:
        result = db.run(sql_query)
        return str(result)
    except Exception as e:
        return str(e)

# tool to generate a sql query from a natural language question
@mcp.tool()
async def get_sql_query(query:str):
    """
    Given a natural language question, generate a SQL query to answer the question.
    and provide only the SQL query as the response given the table schema.
    """
    sql_chain = (
        RunnablePassthrough.assign(schema=get_table_schema)
        | prompt
        | llm.bind(stop="\nSQL Result:")
        | StrOutputParser()
    )
    sql_query = sql_chain.invoke({"question":query})
    return sql_query

if __name__ == "__main__":
    mcp.run(transport="stdio")
    


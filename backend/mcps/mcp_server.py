from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from sqlalchemy import URL
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_anthropic import ChatAnthropic


load_dotenv()

mcp = FastMCP("sql-agent")


#Prompt template
template = """
Based on the table schema below, write a SQL query that would answer the user's question.
{schema}

Question: {question}
SQL Query:

Give only the SQL query as the response. Do not include any explanations or additional text.
"""

prompt = ChatPromptTemplate.from_template(template)

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

llm = ChatAnthropic(model="claude-3-5-haiku-20241022",temperature=0)


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
# @mcp.tool()
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
# @mcp.tool()
async def get_sql_query(query:str):
    """
    Given a natural language question, generate a SQL query to answer the question.
    and provide only the SQL query as the response given the table schema.
    """
    sql_chain = (
        RunnablePassthrough.assign(schema=get_table_schema)
        | prompt
        | llm
        | StrOutputParser()
    )
    sql_query = sql_chain.invoke({"question":query})
    return sql_query

@mcp.tool()
async def get_query_response(query:str):
    """
    Given a natural language question, generate a SQL query to answer the question,
    execute it against the PostgreSQL database, and return the results.
    """
    try:
        sql_query = await get_sql_query(query)
        result = await get_sql_response(sql_query)
        return result
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    mcp.run(transport="stdio")
    


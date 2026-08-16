# Main application entry point
import dash
from dash import Dash

app = Dash(__name__, use_pages=True)

# Only Dashboard + Holdings active
# Other tabs commented out until ready

# import pages.ruler.page
# import pages.house.page
# import pages.economy.page
# import pages.military.page
# import pages.innovations.page
# import pages.council.page
# import pages.goals.page

app.layout = dash.page_container

if __name__ == "__main__":
    app.run(debug=True)

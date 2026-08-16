import dash

app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder="pages"   # CRITICAL
)

app.layout = dash.page_container

if __name__ == "__main__":
    app.run(debug=True)

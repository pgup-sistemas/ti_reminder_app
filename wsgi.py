from app import create_app

app = create_app()  # cria a instância do Flask a partir da factory

if __name__ == "__main__":
    app.run()



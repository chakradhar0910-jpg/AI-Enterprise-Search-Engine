import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "127.0.0.1")
    debug = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    print("\n" + "="*65)
    print("   AI-BASED ENTERPRISE SEARCH ENGINE (RAG & SEMANTIC SEARCH)")
    print("="*65)
    print(f" * Server Running: http://{host}:{port}")
    print(f" * Demo Admin:     admin@enterprise.ai  |  Password: Admin@123456")
    print(f" * Demo User:      user@enterprise.ai   |  Password: User@123456")
    print("="*65 + "\n")

    app.run(host=host, port=port, debug=debug)

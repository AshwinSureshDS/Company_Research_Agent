# backend/app/scripts/populate_pinecone.py
import asyncio
import sys
import os
import json
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.embeddings import generate_embedding
from app.memory import initialize_pinecone, store_memory

async def populate_pinecone_with_company_data():
    """Populate Pinecone with company data from JSON files."""
    # Initialize Pinecone
    pinecone_index = initialize_pinecone()
    
    # Path to company data
    data_dir = Path("d:/College/Company_Research_Chatbot/backend/data/companies")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if there are any company data files
    company_files = list(data_dir.glob("*.json"))
    if not company_files:
        print("No company data files found. Creating sample data...")
        # Create sample data
        sample_companies = [
            {
                "id": "apple",
                "name": "Apple Inc.",
                "description": "Apple Inc. is an American multinational technology company that designs, develops, and sells consumer electronics, computer software, and online services.",
                "industry": "Technology",
                "founded": "April 1, 1976",
                "headquarters": "Cupertino, California, United States",
                "key_products": ["iPhone", "iPad", "Mac", "Apple Watch", "Apple TV", "iOS", "macOS", "watchOS", "tvOS"],
                "key_people": ["Tim Cook (CEO)", "Jeff Williams (COO)", "Luca Maestri (CFO)"]
            },
            {
                "id": "microsoft",
                "name": "Microsoft Corporation",
                "description": "Microsoft Corporation is an American multinational technology company that develops, manufactures, licenses, supports, and sells computer software, consumer electronics, personal computers, and related services.",
                "industry": "Technology",
                "founded": "April 4, 1975",
                "headquarters": "Redmond, Washington, United States",
                "key_products": ["Windows", "Office", "Azure", "Xbox", "Surface", "LinkedIn", "GitHub"],
                "key_people": ["Satya Nadella (CEO)", "Brad Smith (President)", "Amy Hood (CFO)"]
            }
        ]
        
        # Save sample data
        for company in sample_companies:
            with open(data_dir / f"{company['id']}.json", "w") as f:
                json.dump(company, f, indent=2)
        
        company_files = list(data_dir.glob("*.json"))
    
    # Process each company file
    for company_file in company_files:
        print(f"Processing {company_file.name}...")
        with open(company_file, "r") as f:
            company_data = json.load(f)
        
        # Create text chunks from company data
        chunks = []
        
        # Add basic info
        basic_info = f"Company: {company_data.get('name')}\n"
        basic_info += f"Description: {company_data.get('description')}\n"
        basic_info += f"Industry: {company_data.get('industry')}\n"
        basic_info += f"Founded: {company_data.get('founded')}\n"
        basic_info += f"Headquarters: {company_data.get('headquarters')}\n"
        chunks.append(basic_info)
        
        # Add key products
        if "key_products" in company_data:
            products_info = f"Key Products of {company_data.get('name')}:\n"
            for product in company_data["key_products"]:
                products_info += f"- {product}\n"
            chunks.append(products_info)
        
        # Add key people
        if "key_people" in company_data:
            people_info = f"Key People at {company_data.get('name')}:\n"
            for person in company_data["key_people"]:
                people_info += f"- {person}\n"
            chunks.append(people_info)
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = await generate_embedding(chunk)
            if embedding:
                # Store in Pinecone
                metadata = {
                    "company_id": company_data.get("id"),
                    "text": chunk,
                    "chunk_id": i
                }
                key = f"{company_data.get('id')}_chunk_{i}"
                success = store_memory(pinecone_index, key, embedding, metadata)
                if success:
                    print(f"Successfully stored embedding for {key}")
                else:
                    print(f"Failed to store embedding for {key}")
            else:
                print(f"Failed to generate embedding for chunk {i} of {company_data.get('id')}")
    
    print("Finished populating Pinecone with company data.")

if __name__ == "__main__":
    asyncio.run(populate_pinecone_with_company_data())
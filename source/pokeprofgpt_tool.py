"""
title: PokéProfGPT Tool
description: A tool for Open WebUI that integrates with the PokéAPI to provide detailed Pokémon information.
current-functions:
    - name: get_pokemon_details
        description: Fetches detailed information about a Pokémon, including stats, abilities, and evolution chain.
    - name: get_ability_details
        description: Fetches details about a specific Pokémon ability, including its effect and associated Pokémon.
    - name: get_pokemon_location
        description: Retrieves locations where a Pokémon can be found, organized by game version.
    - name: get_pokemon_movelist
        description: Fetches the movelist of a Pokémon, grouped by version group and learn method.
author: q-johnson
version: 0.0.7
license: MIT License
"""

import requests

def get_pokeapi(endpoint: str):
    url = f"https://pokeapi.co/api/v2/{endpoint}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching data from PokeAPI: {response.status_code}")

def format_api_param(name: str) -> str:
    """
    Format parameter names for PokeAPI by replacing spaces with dashes and converting to lowercase.
    :param name: The name to format (e.g., "Tapu Lele")
    :return: Formatted name (e.g., "tapu-lele")
    """
    return name.lower().replace(" ", "-")


def process_evolution_chain(chain_data, evolution_list):
    # Get the evolutions from the current chain node
    evolves_to = chain_data.get("evolves_to", [])
    
    for evolution in evolves_to:
        evolution_details = evolution.get("evolution_details", [{}])[0] if evolution.get("evolution_details") else {}
        
        evolution_info = {
            "name": evolution.get("species", {}).get("name", "Unknown"),
            "trigger": evolution_details.get("trigger", {}).get("name", "Unknown") if evolution_details else "Unknown",
            "min_level": evolution_details.get("min_level"),
            "item": evolution_details.get("item", {}).get("name") if evolution_details.get("item") else None,
            "time_of_day": evolution_details.get("time_of_day") if evolution_details.get("time_of_day") else None,
            "min_happiness": evolution_details.get("min_happiness"),
            "held_item": evolution_details.get("held_item", {}).get("name") if evolution_details.get("held_item") else None,
        }
        
        # Filter out None values for cleaner output
        evolution_info = {k: v for k, v in evolution_info.items() if v is not None}
        evolution_list.append(evolution_info)
        
        # Recursively process the next evolution stage
        process_evolution_chain(evolution, evolution_list)

class Tools:

    def __init__(self):
        self.citation = True
        pass

    def get_pokemon_details(self, pokemon_name: str):
        """
        Fetches details of a Pokémon by its name.
        :param pokemon_name: Name of the Pokémon (case-insensitive).
        :return: JSON response containing Pokémon details.
        """
        formatted_name = format_api_param(pokemon_name)
        endpoint = f"pokemon/{formatted_name}"
        raw_data_pokemon = get_pokeapi(endpoint)

        endpoint_species = f"pokemon-species/{formatted_name}"
        raw_data_species = get_pokeapi(endpoint_species)


        # Process and return the relevant Pokémon details
        processed_data = {
            "name": raw_data_pokemon.get("name"),
            "id": raw_data_pokemon.get("id"),
            "height": f"{raw_data_pokemon.get('height') / 10:.1f} meters",
            "weight": f"{raw_data_pokemon.get('weight') / 10:.1f} kg",
            "stats": {stat["stat"]["name"]: stat["base_stat"] for stat in raw_data_pokemon.get("stats", [])},
            "type": [type_info["type"]["name"] for type_info in raw_data_pokemon.get("types", [])],
            "abilities": [ability["ability"]["name"] for ability in raw_data_pokemon.get("abilities", [])],
            "is_legendary": raw_data_species.get("is_legendary", False),
            "is_mythical": raw_data_species.get("is_mythical", False),
            "is_baby": raw_data_species.get("is_baby", False),
            "flavor_text_descriptions": {entry["flavor_text"] for entry in raw_data_species.get("flavor_text_entries", []) if entry["language"]["name"] == "en"},
            "egg_groups": [egg_group["name"] for egg_group in raw_data_species.get("egg_groups", [])],
        }

        endpoint_evolution = f"evolution-chain/{raw_data_species.get('evolution_chain', {}).get('url', '').split('/')[-2]}"
        raw_data_evolution = get_pokeapi(endpoint_evolution)

        # Process evolution chain
        processed_evolution_data = {
            "base_form": raw_data_evolution.get("chain", {}).get("species", {}).get("name", "Unknown"),
            "evolutions": []
        }
        process_evolution_chain(raw_data_evolution.get("chain", {}), processed_evolution_data["evolutions"])


        return f"""
You are a professor who studies Pokémon. Give a fun description of the Pokémon {processed_data['name']}. Include the following details:
ID: {processed_data['id']}
Height: {processed_data['height']}
Weight: {processed_data['weight']}
Abilities: {', '.join(processed_data['abilities'])}
Type: {', '.join(processed_data['type'])} 
History and Pokémon Descriptions: {chr(10).join(processed_data['flavor_text_descriptions'])} *Note: History and Pokémon descriptions are often poetic and hyperbolic and may not be literal. As a professor in Pokémon studies, you should consider the broader implications of these descriptions.*
Base Stat Total: {sum(processed_data['stats'].values())}
Stats: {', '.join([f"{stat_name}: {stat_value}" for stat_name, stat_value in processed_data['stats'].items()])}

Include the evolution chain of this Pokémon:
{processed_evolution_data['base_form']} evolves into {', '.join([evo['name'] for evo in processed_evolution_data['evolutions']])} based on the following conditions:
{chr(10).join([f"- {evo['name']} (Trigger: {evo['trigger']}, Min Level: {evo.get('min_level', 'N/A')}, Item: {evo.get('item', 'N/A')}, Time of Day: {evo.get('time_of_day', 'N/A')}, Min Happiness: {evo.get('min_happiness', 'N/A')}, Held Item: {evo.get('held_item', 'N/A')})" for evo in processed_evolution_data['evolutions']])}

Include the additional information about the Pokémon, **only** if it is relevant to the query. Otherwise do not include the additional information:
Egg Groups: {', '.join(processed_data['egg_groups'])} *Note: Egg groups are categories that determine which Pokémon can breed with each other.*
Legendary Status: {'Yes' if processed_data['is_legendary'] else 'No'} *Note: Only a few Pokémon are classified as legendary. Do not discuss the legendary status of any Pokémon that is not classified as such.*
Mythical Status: {'Yes' if processed_data['is_mythical'] else 'No'} *Note: Mythical Pokémon are extremely rare and often event-exclusive. Do not discuss the mythical status of any Pokémon that is not classified as such.*
Baby Status: {'Yes' if processed_data['is_baby'] else 'No'} *Note: Baby Pokémon are often pre-evolutions of other Pokémon and are typically smaller and less powerful. Do not discuss the baby status of any Pokémon that is not classified as such.*
"""
    
    def get_ability_details(self, ability_name: str):
        """
        Fetches details of a Pokémon ability by its name.
        :param ability_name: Name of the ability (case-insensitive).
        :return: JSON response containing ability details.
        """
        formatted_name = format_api_param(ability_name)
        endpoint = f"ability/{formatted_name}"
        raw_data = get_pokeapi(endpoint)

        # Process and return the relevant ability details
        processed_data = {
            "name": raw_data.get("name"),
            "effect": next((entry.get("effect", "") for entry in raw_data.get("effect_entries", []) 
                          if entry.get("language", {}).get("name") == "en"), 
                         "No effect description available in English."),
            "pokemon": [f"{pokemon['pokemon']['name']}{' (Hidden)' if pokemon['is_hidden'] else ''}" for pokemon in raw_data.get("pokemon", [])]
        }
        return f"""
You are a Pokémon expert. Describe the ability {processed_data['name']} in detail. Include the following information:
Effect: {processed_data['effect']}
Pokémon with this ability: {', '.join(processed_data['pokemon'])}
"""
    
    def get_pokemon_location(self, pokemon_name: str):
        """
        Fetches locations where a Pokémon can be found, organized by game version.
        :param pokemon_name: Name of the Pokémon (case-insensitive).
        :return: JSON response containing location details sorted by game version.
        """
        formatted_name = format_api_param(pokemon_name)
        endpoint = f"pokemon/{formatted_name}/encounters"
        raw_data = get_pokeapi(endpoint)

        # Group locations by game version
        locations_by_version = {}
        
        for encounter in raw_data:
            location_name = encounter["location_area"]["name"].replace("-", " ").title()
            
            for version_detail in encounter["version_details"]:
                version_name = version_detail["version"]["name"]
                
                if version_name not in locations_by_version:
                    locations_by_version[version_name] = []
                    
                if location_name not in locations_by_version[version_name]:
                    locations_by_version[version_name].append(location_name)
        
        # Format the output with locations organized by version
        if not locations_by_version:
            return f"""
You are a Pokémon researcher. Provide information on where the Pokémon {pokemon_name} can be found in the wild.
Unfortunately, no location data is available for this Pokémon in the database.
"""
        
        # Build a formatted version-to-locations mapping for the prompt
        formatted_locations = []
        for version, locations in sorted(locations_by_version.items()):
            formatted_locations.append(f"- {version.title()}: {', '.join(locations)}")
        
        return f"""
You are a Pokémon researcher. Provide information on where the Pokémon {pokemon_name} can be found in the wild.
The Pokémon can be found in these locations across various games:

{chr(10).join(formatted_locations)}

Based on this information, describe where players might encounter this Pokémon in the wild. Do not summarize locational data. Offer all locations for every region and game.
"""

    def get_pokemon_movelist(self, pokemon_name: str):
        """
        Fetches the movelist of a Pokémon by its name, grouped by version group.
        :param pokemon_name: Name of the Pokémon (case-insensitive).
        :return: Formatted markdown tables of moves organized by version group.
        """
        formatted_name = format_api_param(pokemon_name)
        endpoint = f"pokemon/{formatted_name}"
        raw_data = get_pokeapi(endpoint)

        # Group moves by version_group
        moves_by_version = {}
        
        for move in raw_data.get("moves", []):
            move_name = move["move"]["name"].replace("-", " ").title()
            
            for version_detail in move["version_group_details"]:
                version_group = version_detail["version_group"]["name"]
                learn_method = version_detail["move_learn_method"]["name"]
                level_learned_at = version_detail["level_learned_at"]
                
                if version_group not in moves_by_version:
                    moves_by_version[version_group] = []
                    
                moves_by_version[version_group].append({
                    "name": move_name,
                    "learn_method": learn_method,
                    "level_learned_at": level_learned_at
                })
        
        # Format the output as markdown tables by version group
        if not moves_by_version:
            return f"No move data available for {pokemon_name}."
        
        # Create markdown tables for each version group
        markdown_tables = []
        for version_group, moves in sorted(moves_by_version.items()):
            # Sort moves: first by learn method, then by level (if applicable), then by name
            moves.sort(key=lambda x: (x["learn_method"], x["level_learned_at"] if x["level_learned_at"] else 0, x["name"]))
            
            table = f"### {version_group.replace('-', ' ').title()}\n\n"
            table += "| Move | Learn Method | Level |\n"
            table += "|------|-------------|-------|\n"
            
            for move in moves:
                level = str(move["level_learned_at"]) if move["level_learned_at"] else "N/A"
                table += f"| {move['name']} | {move['learn_method'].replace('-', ' ').title()} | {level} |\n"
            
            markdown_tables.append(table)
        
        return f"""
Provide information about the moves that {pokemon_name.title()} can learn across different game versions. If there is a specific game version asked about, include only the moves available in that version. If no game version is specified, provide all moves across all versions.
{chr(10).join(markdown_tables)}

"""

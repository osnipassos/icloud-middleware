from carddav import get_contacts_raw, parse_vcards
import json

resultado = get_contacts_raw()
if "vcard" in resultado:
    contatos = parse_vcards(resultado["vcard"])
    print(json.dumps(contatos, indent=2, ensure_ascii=False))
else:
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
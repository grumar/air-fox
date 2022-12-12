from homeassistant import core
import BeautifulSoup
import http.client

async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Air Fox Integration component."""
    # @TODO: Add setup code.

    conn = http.client.HTTPConnection("air-fox.pl")
    conn.request("GET", "/")
    r1 = conn.getresponse()

    soup = BeautifulSoup.BeautifulSoup(r1)
    inp = soup.find("input", {"id": "test1"})
    
    
    print(inp);
    return True

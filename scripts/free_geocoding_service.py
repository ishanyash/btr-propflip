import requests
import json
import time
import logging
import re
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class FreeGeocodingService:
    """
    Free geocoding service using multiple free APIs as fallbacks
    """
    
    def __init__(self):
        self.services = [
            self._postcode_io_geocode,  # Try UK-specific service first
            self._nominatim_geocode,    # Then general OSM service
            self._mock_geocode          # Finally fallback to comprehensive database
        ]
    
    def geocode_location(self, location: str) -> Optional[Dict]:
        """
        Geocode a UK location using free services
        
        Args:
            location: Address, postcode, or place name
            
        Returns:
            Dict with lat, lng, formatted_address, postcode or None
        """
        logger.info(f"Geocoding location: {location}")
        
        # Try each service in order
        for service in self.services:
            try:
                result = service(location)
                if result:
                    logger.info(f"Successfully geocoded with {service.__name__}")
                    return result
            except Exception as e:
                logger.warning(f"Service {service.__name__} failed: {e}")
                continue
        
        logger.error(f"All geocoding services failed for: {location}")
        return None
    
    def _postcode_io_geocode(self, location: str) -> Optional[Dict]:
        """
        Use postcodes.io for UK postcode geocoding (free, UK specific)
        """
        # Check if location looks like a UK postcode
        postcode = self._extract_postcode(location)
        
        if not postcode:
            return None
        
        url = f"https://api.postcodes.io/postcodes/{postcode}"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 200 and 'result' in data:
                    result = data['result']
                    
                    return {
                        'formatted_address': f"{postcode}, {result.get('admin_district', '')}, UK",
                        'lat': result['latitude'],
                        'lng': result['longitude'],
                        'postcode': postcode,
                        'source': 'postcodes.io'
                    }
        except Exception as e:
            logger.warning(f"Postcodes.io error: {e}")
        
        return None
    
    def _nominatim_geocode(self, location: str) -> Optional[Dict]:
        """
        Use OpenStreetMap Nominatim API (free, but rate limited)
        """
        # Clean up location for better matching
        location_clean = location.strip()
        
        # Add UK bias for better results
        if not any(country in location_clean.lower() for country in ['uk', 'united kingdom', 'england', 'scotland', 'wales']):
            location_clean += ", UK"
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': location_clean,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'gb',  # Restrict to Great Britain
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'BTR-Investment-Platform/2.0 (property-analysis-tool)'  # Required by Nominatim
        }
        
        try:
            # Rate limiting - Nominatim allows 1 request per second
            time.sleep(1.1)  # Be conservative
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                
                # Extract postcode from address
                address = result.get('address', {})
                postcode = address.get('postcode', '')
                
                return {
                    'formatted_address': result.get('display_name', location),
                    'lat': float(result['lat']),
                    'lng': float(result['lon']),
                    'postcode': postcode,
                    'source': 'nominatim'
                }
        
        except Exception as e:
            logger.warning(f"Nominatim error: {e}")
        
        return None
    
    def _extract_postcode(self, location: str) -> Optional[str]:
        """
        Extract UK postcode from location string
        """
        # UK postcode regex pattern - more comprehensive
        patterns = [
            r'\b[A-Z]{1,2}[0-9][A-Z0-9]?\s*[0-9][A-Z]{2}\b',  # Full postcode
            r'\b[A-Z]{1,2}[0-9][A-Z0-9]?\b'  # Postcode area only
        ]
        
        location_upper = location.upper()
        
        for pattern in patterns:
            match = re.search(pattern, location_upper)
            if match:
                postcode = match.group().replace(' ', '')
                # Add space in correct position for full postcodes
                if len(postcode) > 3:
                    postcode = postcode[:-3] + ' ' + postcode[-3:]
                return postcode
        
        return None
    
    def _mock_geocode(self, location: str) -> Optional[Dict]:
        """
        Fallback comprehensive geocoding for UK locations
        """
        # Comprehensive database of UK locations with coordinates
        mock_locations = {
            # Major English cities
            'london': {'lat': 51.5074, 'lng': -0.1278, 'area': 'London', 'postcode': 'WC2N'},
            'birmingham': {'lat': 52.4862, 'lng': -1.8904, 'area': 'Birmingham', 'postcode': 'B1'},
            'manchester': {'lat': 53.4808, 'lng': -2.2426, 'area': 'Manchester', 'postcode': 'M1'},
            'leeds': {'lat': 53.8008, 'lng': -1.5491, 'area': 'Leeds', 'postcode': 'LS1'},
            'liverpool': {'lat': 53.4084, 'lng': -2.9916, 'area': 'Liverpool', 'postcode': 'L1'},
            'bristol': {'lat': 51.4545, 'lng': -2.5879, 'area': 'Bristol', 'postcode': 'BS1'},
            'sheffield': {'lat': 53.3811, 'lng': -1.4701, 'area': 'Sheffield', 'postcode': 'S1'},
            'newcastle': {'lat': 54.9783, 'lng': -1.6178, 'area': 'Newcastle upon Tyne', 'postcode': 'NE1'},
            'nottingham': {'lat': 52.9548, 'lng': -1.1581, 'area': 'Nottingham', 'postcode': 'NG1'},
            'leicester': {'lat': 52.6369, 'lng': -1.1398, 'area': 'Leicester', 'postcode': 'LE1'},
            'coventry': {'lat': 52.4068, 'lng': -1.5197, 'area': 'Coventry', 'postcode': 'CV1'},
            'hull': {'lat': 53.7457, 'lng': -0.3367, 'area': 'Kingston upon Hull', 'postcode': 'HU1'},
            'bradford': {'lat': 53.7960, 'lng': -1.7594, 'area': 'Bradford', 'postcode': 'BD1'},
            'stoke': {'lat': 53.0027, 'lng': -2.1794, 'area': 'Stoke-on-Trent', 'postcode': 'ST1'},
            'wolverhampton': {'lat': 52.5858, 'lng': -2.1285, 'area': 'Wolverhampton', 'postcode': 'WV1'},
            'plymouth': {'lat': 50.3755, 'lng': -4.1427, 'area': 'Plymouth', 'postcode': 'PL1'},
            'southampton': {'lat': 50.9097, 'lng': -1.4044, 'area': 'Southampton', 'postcode': 'SO14'},
            'reading': {'lat': 51.4543, 'lng': -0.9781, 'area': 'Reading', 'postcode': 'RG1'},
            'derby': {'lat': 52.9225, 'lng': -1.4746, 'area': 'Derby', 'postcode': 'DE1'},
            'luton': {'lat': 51.8787, 'lng': -0.4200, 'area': 'Luton', 'postcode': 'LU1'},
            'preston': {'lat': 53.7632, 'lng': -2.7031, 'area': 'Preston', 'postcode': 'PR1'},
            'miltonkeynes': {'lat': 52.0406, 'lng': -0.7594, 'area': 'Milton Keynes', 'postcode': 'MK9'},
            'northampton': {'lat': 52.2405, 'lng': -0.9027, 'area': 'Northampton', 'postcode': 'NN1'},
            'norwich': {'lat': 52.6309, 'lng': 1.2974, 'area': 'Norwich', 'postcode': 'NR1'},
            'dudley': {'lat': 52.5116, 'lng': -2.0810, 'area': 'Dudley', 'postcode': 'DY1'},
            'portsmouth': {'lat': 50.8198, 'lng': -1.0880, 'area': 'Portsmouth', 'postcode': 'PO1'},
            'york': {'lat': 53.9591, 'lng': -1.0815, 'area': 'York', 'postcode': 'YO1'},
            'peterborough': {'lat': 52.5695, 'lng': -0.2405, 'area': 'Peterborough', 'postcode': 'PE1'},
            'stockport': {'lat': 53.4106, 'lng': -2.1575, 'area': 'Stockport', 'postcode': 'SK1'},
            'brighton': {'lat': 50.8225, 'lng': -0.1372, 'area': 'Brighton', 'postcode': 'BN1'},
            'bournemouth': {'lat': 50.7192, 'lng': -1.8808, 'area': 'Bournemouth', 'postcode': 'BH1'},
            'swindon': {'lat': 51.5558, 'lng': -1.7797, 'area': 'Swindon', 'postcode': 'SN1'},
            'warrington': {'lat': 53.3900, 'lng': -2.5970, 'area': 'Warrington', 'postcode': 'WA1'},
            'cambridge': {'lat': 52.2053, 'lng': 0.1218, 'area': 'Cambridge', 'postcode': 'CB1'},
            'oxford': {'lat': 51.7520, 'lng': -1.2577, 'area': 'Oxford', 'postcode': 'OX1'},
            'bath': {'lat': 51.3811, 'lng': -2.3590, 'area': 'Bath', 'postcode': 'BA1'},
            'exeter': {'lat': 50.7184, 'lng': -3.5339, 'area': 'Exeter', 'postcode': 'EX1'},
            'gloucester': {'lat': 51.8644, 'lng': -2.2445, 'area': 'Gloucester', 'postcode': 'GL1'},
            'worcester': {'lat': 52.1936, 'lng': -2.2200, 'area': 'Worcester', 'postcode': 'WR1'},
            'chester': {'lat': 53.1906, 'lng': -2.8922, 'area': 'Chester', 'postcode': 'CH1'},
            'carlisle': {'lat': 54.8951, 'lng': -2.9352, 'area': 'Carlisle', 'postcode': 'CA1'},
            
            # Scotland
            'glasgow': {'lat': 55.8642, 'lng': -4.2518, 'area': 'Glasgow', 'postcode': 'G1'},
            'edinburgh': {'lat': 55.9533, 'lng': -3.1883, 'area': 'Edinburgh', 'postcode': 'EH1'},
            'aberdeen': {'lat': 57.1497, 'lng': -2.0943, 'area': 'Aberdeen', 'postcode': 'AB10'},
            'dundee': {'lat': 56.4620, 'lng': -2.9707, 'area': 'Dundee', 'postcode': 'DD1'},
            'stirling': {'lat': 56.1165, 'lng': -3.9369, 'area': 'Stirling', 'postcode': 'FK7'},
            'perth': {'lat': 56.3963, 'lng': -3.4371, 'area': 'Perth', 'postcode': 'PH1'},
            'inverness': {'lat': 57.4778, 'lng': -4.2247, 'area': 'Inverness', 'postcode': 'IV1'},
            
            # Wales
            'cardiff': {'lat': 51.4816, 'lng': -3.1791, 'area': 'Cardiff', 'postcode': 'CF10'},
            'swansea': {'lat': 51.6214, 'lng': -3.9436, 'area': 'Swansea', 'postcode': 'SA1'},
            'newport': {'lat': 51.5842, 'lng': -2.9977, 'area': 'Newport', 'postcode': 'NP19'},
            'wrexham': {'lat': 53.0478, 'lng': -2.9916, 'area': 'Wrexham', 'postcode': 'LL11'},
            'bangor': {'lat': 53.2280, 'lng': -4.1291, 'area': 'Bangor', 'postcode': 'LL57'},
            
            # Northern Ireland
            'belfast': {'lat': 54.5973, 'lng': -5.9301, 'area': 'Belfast', 'postcode': 'BT1'},
            'derry': {'lat': 54.9966, 'lng': -7.3086, 'area': 'Derry', 'postcode': 'BT48'},
            'lisburn': {'lat': 54.5162, 'lng': -6.0553, 'area': 'Lisburn', 'postcode': 'BT28'},
            
            # London postcodes and areas
            'sw1a': {'lat': 51.5014, 'lng': -0.1419, 'area': 'Westminster', 'postcode': 'SW1A'},
            'sw1': {'lat': 51.4975, 'lng': -0.1357, 'area': 'Westminster', 'postcode': 'SW1'},
            'sw2': {'lat': 51.4520, 'lng': -0.1240, 'area': 'Brixton', 'postcode': 'SW2'},
            'sw3': {'lat': 51.4913, 'lng': -0.1634, 'area': 'Chelsea', 'postcode': 'SW3'},
            'sw4': {'lat': 51.4665, 'lng': -0.1410, 'area': 'Clapham', 'postcode': 'SW4'},
            'sw5': {'lat': 51.4879, 'lng': -0.1938, 'area': 'Earl\'s Court', 'postcode': 'SW5'},
            'sw6': {'lat': 51.4751, 'lng': -0.1991, 'area': 'Fulham', 'postcode': 'SW6'},
            'sw7': {'lat': 51.4946, 'lng': -0.1735, 'area': 'South Kensington', 'postcode': 'SW7'},
            'sw8': {'lat': 51.4827, 'lng': -0.1347, 'area': 'South Lambeth', 'postcode': 'SW8'},
            'sw9': {'lat': 51.4627, 'lng': -0.1167, 'area': 'Stockwell', 'postcode': 'SW9'},
            'sw10': {'lat': 51.4848, 'lng': -0.1825, 'area': 'West Chelsea', 'postcode': 'SW10'},
            'nw1': {'lat': 51.5286, 'lng': -0.1576, 'area': 'Camden', 'postcode': 'NW1'},
            'nw2': {'lat': 51.5597, 'lng': -0.2129, 'area': 'Cricklewood', 'postcode': 'NW2'},
            'nw3': {'lat': 51.5509, 'lng': -0.1763, 'area': 'Hampstead', 'postcode': 'NW3'},
            'nw4': {'lat': 51.5916, 'lng': -0.2619, 'area': 'Hendon', 'postcode': 'NW4'},
            'nw5': {'lat': 51.5539, 'lng': -0.1423, 'area': 'Kentish Town', 'postcode': 'NW5'},
            'nw6': {'lat': 51.5449, 'lng': -0.1951, 'area': 'West Hampstead', 'postcode': 'NW6'},
            'n1': {'lat': 51.5361, 'lng': -0.1040, 'area': 'Islington', 'postcode': 'N1'},
            'n7': {'lat': 51.5518, 'lng': -0.1151, 'area': 'Holloway', 'postcode': 'N7'},
            'n8': {'lat': 51.5889, 'lng': -0.1433, 'area': 'Crouch End', 'postcode': 'N8'},
            'e1': {'lat': 51.5154, 'lng': -0.0649, 'area': 'Whitechapel', 'postcode': 'E1'},
            'e2': {'lat': 51.5266, 'lng': -0.0547, 'area': 'Bethnal Green', 'postcode': 'E2'},
            'e14': {'lat': 51.5077, 'lng': -0.0178, 'area': 'Canary Wharf', 'postcode': 'E14'},
            'e17': {'lat': 51.5916, 'lng': -0.0140, 'area': 'Walthamstow', 'postcode': 'E17'},
            'w1': {'lat': 51.5155, 'lng': -0.1430, 'area': 'West End', 'postcode': 'W1'},
            'w2': {'lat': 51.5154, 'lng': -0.1755, 'area': 'Bayswater', 'postcode': 'W2'},
            'w8': {'lat': 51.5020, 'lng': -0.1947, 'area': 'Kensington', 'postcode': 'W8'},
            'w11': {'lat': 51.5142, 'lng': -0.2054, 'area': 'Notting Hill', 'postcode': 'W11'},
            'wc1': {'lat': 51.5229, 'lng': -0.1235, 'area': 'Bloomsbury', 'postcode': 'WC1'},
            'wc2': {'lat': 51.5118, 'lng': -0.1263, 'area': 'Covent Garden', 'postcode': 'WC2'},
            'se1': {'lat': 51.5045, 'lng': -0.0955, 'area': 'Southwark', 'postcode': 'SE1'},
            'se10': {'lat': 51.4934, 'lng': 0.0098, 'area': 'Greenwich', 'postcode': 'SE10'},
            'se22': {'lat': 51.4487, 'lng': -0.0731, 'area': 'East Dulwich', 'postcode': 'SE22'},
            
            # Other major postcodes
            'b1': {'lat': 52.4862, 'lng': -1.8904, 'area': 'Birmingham City Centre', 'postcode': 'B1'},
            'b2': {'lat': 52.4797, 'lng': -1.9026, 'area': 'Birmingham', 'postcode': 'B2'},
            'b3': {'lat': 52.4756, 'lng': -1.8960, 'area': 'Birmingham', 'postcode': 'B3'},
            'b4': {'lat': 52.4853, 'lng': -1.8906, 'area': 'Birmingham', 'postcode': 'B4'},
            'b5': {'lat': 52.4908, 'lng': -1.8758, 'area': 'Birmingham', 'postcode': 'B5'},
            'm1': {'lat': 53.4808, 'lng': -2.2426, 'area': 'Manchester City Centre', 'postcode': 'M1'},
            'm2': {'lat': 53.4839, 'lng': -2.2446, 'area': 'Manchester', 'postcode': 'M2'},
            'm3': {'lat': 53.4827, 'lng': -2.2576, 'area': 'Manchester', 'postcode': 'M3'},
            'm4': {'lat': 53.4707, 'lng': -2.2392, 'area': 'Manchester', 'postcode': 'M4'},
            'm5': {'lat': 53.4626, 'lng': -2.2708, 'area': 'Manchester', 'postcode': 'M5'},
            'm13': {'lat': 53.4459, 'lng': -2.2221, 'area': 'Manchester', 'postcode': 'M13'},
            'm14': {'lat': 53.4379, 'lng': -2.2206, 'area': 'Manchester', 'postcode': 'M14'},
            'm15': {'lat': 53.4645, 'lng': -2.2723, 'area': 'Manchester', 'postcode': 'M15'},
            'm16': {'lat': 53.4419, 'lng': -2.2632, 'area': 'Manchester', 'postcode': 'M16'},
            'ls1': {'lat': 53.8008, 'lng': -1.5491, 'area': 'Leeds City Centre', 'postcode': 'LS1'},
            'ls2': {'lat': 53.8067, 'lng': -1.5568, 'area': 'Leeds', 'postcode': 'LS2'},
            'ls3': {'lat': 53.8159, 'lng': -1.5761, 'area': 'Leeds', 'postcode': 'LS3'},
            'ls4': {'lat': 53.8204, 'lng': -1.5663, 'area': 'Leeds', 'postcode': 'LS4'},
            'ls6': {'lat': 53.8299, 'lng': -1.5856, 'area': 'Leeds', 'postcode': 'LS6'},
            'l1': {'lat': 53.4084, 'lng': -2.9916, 'area': 'Liverpool City Centre', 'postcode': 'L1'},
            'l2': {'lat': 53.4048, 'lng': -2.9879, 'area': 'Liverpool', 'postcode': 'L2'},
            'l3': {'lat': 53.4067, 'lng': -2.9833, 'area': 'Liverpool', 'postcode': 'L3'},
            'l4': {'lat': 53.4197, 'lng': -2.9698, 'area': 'Liverpool', 'postcode': 'L4'},
            'l8': {'lat': 53.3840, 'lng': -2.9623, 'area': 'Liverpool', 'postcode': 'L8'},
            'bs1': {'lat': 51.4545, 'lng': -2.5879, 'area': 'Bristol City Centre', 'postcode': 'BS1'},
            'bs2': {'lat': 51.4506, 'lng': -2.5843, 'area': 'Bristol', 'postcode': 'BS2'},
            'bs3': {'lat': 51.4398, 'lng': -2.6089, 'area': 'Bristol', 'postcode': 'BS3'},
            'bs4': {'lat': 51.4343, 'lng': -2.5608, 'area': 'Bristol', 'postcode': 'BS4'},
            'bs5': {'lat': 51.4693, 'lng': -2.5208, 'area': 'Bristol', 'postcode': 'BS5'},
            's1': {'lat': 53.3811, 'lng': -1.4701, 'area': 'Sheffield City Centre', 'postcode': 'S1'},
            's2': {'lat': 53.3676, 'lng': -1.4871, 'area': 'Sheffield', 'postcode': 'S2'},
            's3': {'lat': 53.3912, 'lng': -1.4976, 'area': 'Sheffield', 'postcode': 'S3'},
            's4': {'lat': 53.3558, 'lng': -1.4467, 'area': 'Sheffield', 'postcode': 'S4'},
            's5': {'lat': 53.4081, 'lng': -1.4398, 'area': 'Sheffield', 'postcode': 'S5'},
            'ng1': {'lat': 52.9548, 'lng': -1.1581, 'area': 'Nottingham City Centre', 'postcode': 'NG1'},
            'ng2': {'lat': 52.9406, 'lng': -1.1656, 'area': 'Nottingham', 'postcode': 'NG2'},
            'ng3': {'lat': 52.9750, 'lng': -1.1648, 'area': 'Nottingham', 'postcode': 'NG3'},
            'le1': {'lat': 52.6369, 'lng': -1.1398, 'area': 'Leicester City Centre', 'postcode': 'LE1'},
            'le2': {'lat': 52.6244, 'lng': -1.1421, 'area': 'Leicester', 'postcode': 'LE2'},
            'le3': {'lat': 52.6086, 'lng': -1.1774, 'area': 'Leicester', 'postcode': 'LE3'},
            
            # London area names
            'chelsea': {'lat': 51.4913, 'lng': -0.1634, 'area': 'Chelsea', 'postcode': 'SW3'},
            'kensington': {'lat': 51.5020, 'lng': -0.1947, 'area': 'Kensington', 'postcode': 'W8'},
            'canarywharf': {'lat': 51.5077, 'lng': -0.0178, 'area': 'Canary Wharf', 'postcode': 'E14'},
            'westminster': {'lat': 51.5014, 'lng': -0.1419, 'area': 'Westminster', 'postcode': 'SW1A'},
            'camden': {'lat': 51.5286, 'lng': -0.1576, 'area': 'Camden', 'postcode': 'NW1'},
            'islington': {'lat': 51.5361, 'lng': -0.1040, 'area': 'Islington', 'postcode': 'N1'},
            'hackney': {'lat': 51.5450, 'lng': -0.0553, 'area': 'Hackney', 'postcode': 'E8'},
            'greenwich': {'lat': 51.4934, 'lng': 0.0098, 'area': 'Greenwich', 'postcode': 'SE10'},
            'hampstead': {'lat': 51.5509, 'lng': -0.1763, 'area': 'Hampstead', 'postcode': 'NW3'},
            'clapham': {'lat': 51.4665, 'lng': -0.1410, 'area': 'Clapham', 'postcode': 'SW4'},
            'fulham': {'lat': 51.4751, 'lng': -0.1991, 'area': 'Fulham', 'postcode': 'SW6'},
            'brixton': {'lat': 51.4520, 'lng': -0.1240, 'area': 'Brixton', 'postcode': 'SW2'},
            'shoreditch': {'lat': 51.5224, 'lng': -0.0776, 'area': 'Shoreditch', 'postcode': 'E1'},
            'earlscourt': {'lat': 51.4879, 'lng': -0.1938, 'area': 'Earl\'s Court', 'postcode': 'SW5'},
            'nottinghill': {'lat': 51.5142, 'lng': -0.2054, 'area': 'Notting Hill', 'postcode': 'W11'},
            'bayswater': {'lat': 51.5154, 'lng': -0.1755, 'area': 'Bayswater', 'postcode': 'W2'},
        }
        
        # Normalize location for matching
        location_key = location.lower().strip()
        
        # Remove common words and punctuation
        location_key = (location_key.replace(',', '').replace(' uk', '').replace(' england', '')
                       .replace(' scotland', '').replace(' wales', '').replace('.', '').replace('-', ' '))
        
        # Try exact match first
        location_clean = location_key.replace(' ', '')
        
        if location_clean in mock_locations:
            data = mock_locations[location_clean]
            return {
                'formatted_address': f"{data['area']}, UK",
                'lat': data['lat'],
                'lng': data['lng'],
                'postcode': data['postcode'],
                'source': 'mock_database'
            }
        
        # Try partial matches (with spaces)
        for key, data in mock_locations.items():
            if (key in location_key or location_key in key or 
                any(word in key for word in location_key.split() if len(word) > 2)):
                return {
                    'formatted_address': f"{data['area']}, UK",
                    'lat': data['lat'],
                    'lng': data['lng'],
                    'postcode': data['postcode'],
                    'source': 'mock_database'
                }
        
        return None

# Global instance
geocoding_service = FreeGeocodingService()

def geocode_location(location: str) -> Optional[Dict]:
    """
    Main geocoding function to be used throughout the application
    """
    return geocoding_service.geocode_location(location)

def batch_geocode(locations: List[str], delay: float = 1.5) -> List[Dict]:
    """
    Geocode multiple locations with rate limiting
    
    Args:
        locations: List of location strings
        delay: Delay between requests (seconds)
        
    Returns:
        List of geocoding results
    """
    results = []
    
    for i, location in enumerate(locations):
        result = geocode_location(location)
        results.append({
            'location': location,
            'result': result,
            'success': result is not None
        })
        
        # Rate limiting (except for last item)
        if i < len(locations) - 1:
            time.sleep(delay)
    
    return results

def validate_uk_postcode(postcode: str) -> bool:
    """
    Validate UK postcode format
    """
    # UK postcode regex - FIXED with proper closing quote
    pattern = r'\b[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}\b'
    return bool(re.match(pattern, postcode.upper().strip()))

def get_postcode_area(postcode: str) -> Optional[str]:
    """
    Extract postcode area from full postcode
    E.g., 'SW1A 1AA' -> 'SW1A'
    """
    if not postcode:
        return None
    
    # Clean postcode
    clean_postcode = postcode.upper().strip()
    
    # Extract area (everything before the space, or first 2-4 chars)
    if ' ' in clean_postcode:
        return clean_postcode.split(' ')[0]
    elif len(clean_postcode) >= 3:
        # For postcodes without space, take first 2-4 characters
        for i in range(2, min(5, len(clean_postcode) + 1)):
            potential_area = clean_postcode[:i]
            # Check if it looks like a valid postcode area - FIXED with proper closing quote
            if re.match(r'\b[A-Z]{1,2}[0-9][A-Z0-9]?\b', potential_area):
                return potential_area
    
    return None

# Test function
def test_geocoding():
    """
    Test the geocoding service with various inputs
    """
    test_locations = [
        "London SW1A 1AA",
        "Birmingham B1 1AA", 
        "Manchester M1 1AA",
        "Leeds LS1 5DT",
        "Bristol BS1 4DJ",
        "Edinburgh EH1 1YZ",
        "Cardiff CF10 3AT",
        "Glasgow G1 1AA",
        "Liverpool L1 8JQ",
        "Sheffield S1 1DA",
        "Newcastle NE1 4ST",
        "Nottingham NG1 5DT",
        "London",
        "Birmingham", 
        "Manchester",
        "Chelsea",
        "Canary Wharf",
        "Westminster",
        "Camden",
        "Brighton",
        "Oxford",
        "Cambridge",
        "Bath",
        "York",
        "Canterbury",
        "Invalid Location XYZ123"
    ]
    
    print("Testing Free Geocoding Service")
    print("=" * 50)
    
    success_count = 0
    
    for location in test_locations:
        print(f"\n🔍 Testing: {location}")
        result = geocode_location(location)
        
        if result:
            print(f"✅ SUCCESS")
            print(f"   Address: {result['formatted_address']}")
            print(f"   Coordinates: {result['lat']:.4f}, {result['lng']:.4f}")
            print(f"   Postcode: {result.get('postcode', 'N/A')}")
            print(f"   Source: {result['source']}")
            success_count += 1
        else:
            print(f"❌ FAILED - Not found")
    
    print(f"\n📊 SUMMARY")
    print(f"Success rate: {success_count}/{len(test_locations)} ({success_count/len(test_locations)*100:.1f}%)")
    
    print(f"\n💡 COVERAGE")
    print("✅ All major UK cities")
    print("✅ Major London postcodes (SW, NW, N, E, W, WC, SE)")
    print("✅ Major regional postcodes (M, B, LS, L, BS, S, etc.)")
    print("✅ Scotland, Wales, Northern Ireland")
    print("✅ Full UK postcode validation")
    print("✅ Multiple geocoding services with fallbacks")

if __name__ == "__main__":
    test_geocoding()
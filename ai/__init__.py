# ai/__init__.py
"""
AI Universe - Professional AI Assistants Package
25 ta professional AI xizmati

Bismillah - Professional AI Platform
"""

from .chat_ai import ChatAI
from .tarjimon_ai import TarjimonAI
from .blockchain_ai import BlockchainAI
from .tadqiqot_ai import TadqiqotAI
from .smart_energy_ai import SmartEnergyAI
from .dasturlash_ai import DasturlashAI
from .tibbiy_ai import TibbiyAI
from .talim_ai import TalimAI
from .biznes_ai import BiznesAI
from .huquq_ai import HuquqAI
from .psixologik_ai import PsixologikAI
from .moliya_ai import MoliyaAI
from .sayohat_ai import SayohatAI
from .oshpazlik_ai import OshpazlikAI
from .ijod_ai import IjodAI
from .musiqa_ai import MusiqaAI
from .sport_ai import SportAI
from .ob_havo_ai import ObHavoAI
from .yangiliklar_ai import YangiliklarAI
from .matematik_ai import MatematikAI
from .fan_ai import FanAI
from .ovozli_ai import OvozliAI
from .arxitektura_ai import ArxitekturaAI
from .ekologiya_ai import EkologiyaAI
from .oyin_ai import OyinAI

__all__ = [
    'ChatAI',
    'TarjimonAI', 
    'BlockchainAI',
    'TadqiqotAI',
    'SmartEnergyAI',
    'DasturlashAI',
    'TibbiyAI',
    'TalimAI',
    'BiznesAI',
    'HuquqAI',
    'PsixologikAI',
    'MoliyaAI',
    'SayohatAI',
    'OshpazlikAI',
    'IjodAI',
    'MusiqaAI',
    'SportAI',
    'ObhavaAI',
    'YangiliklarAI',
    'MatematikAI',
    'FanAI',
    'OvozliAI',
    'ArxitekturaAI',
    'EkologiyaAI',
    'OyunAI'
]

# AI Assistant metadata
AI_METADATA = {
    'chat': {
        'name': 'Chat AI',
        'description': 'Umumiy savollar va har kunlik yordamchi',
        'icon': '💬',
        'category': 'general'
    },
    'tarjimon': {
        'name': 'Tarjimon AI', 
        'description': '100+ tilga professional tarjima',
        'icon': '🌐',
        'category': 'language'
    },
    'blockchain': {
        'name': 'Blockchain AI',
        'description': 'Blockchain va kripto texnologiyalar bo\'yicha maslahatchi',
        'icon': '🚀', 
        'category': 'technology'
    },
    'tadqiqot': {
        'name': 'AI Tadqiqot',
        'description': 'Sun\'iy intellekt tadqiqotlari va innovatsion yechimlar',
        'icon': '🧠',
        'category': 'research'
    },
    'smart_energy': {
        'name': 'Smart Energy AI',
        'description': 'Aqlli energiya tizimlari va yashil texnologiyalar',
        'icon': '⚡',
        'category': 'energy'
    },
    'dasturlash': {
        'name': 'Dasturlash AI',
        'description': 'Dasturlash yordamchisi va kod yozuvchi',
        'icon': '💻',
        'category': 'programming'
    },
    'tibbiy': {
        'name': 'Tibbiy AI',
        'description': 'Sog\'liq maslahatchi va tibbiy ma\'lumotlar',
        'icon': '🏥',
        'category': 'medical'
    },
    'talim': {
        'name': 'Ta\'lim AI',
        'description': 'O\'qituvchi va ta\'lim mentori',
        'icon': '🎓',
        'category': 'education'
    }
}
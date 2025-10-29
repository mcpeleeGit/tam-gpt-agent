import json
import os
from datetime import datetime

class DataManager:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.files = {
            'customers': os.path.join(data_dir, 'customers.json'),
            'tickets': os.path.join(data_dir, 'tickets.json'),
            'block_requests': os.path.join(data_dir, 'block_requests.json'),
            'developers': os.path.join(data_dir, 'developers.json'),
            'app_logs': os.path.join(data_dir, 'app_logs.json')
        }
        
        # 초기 데이터 생성
        self._initialize_data()
    
    def _initialize_data(self):
        """초기 데이터 파일이 없으면 생성"""
        for key, filepath in self.files.items():
            if not os.path.exists(filepath):
                self._write_json(filepath, [])
    
    def _read_json(self, filepath):
        """JSON 파일 읽기"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _write_json(self, filepath, data):
        """JSON 파일 쓰기"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ========== 고객 정보 ==========
    def get_customer(self, customer_id):
        """고객 정보 조회"""
        customers = self._read_json(self.files['customers'])
        return next((c for c in customers if c.get('customer_id') == customer_id), None)
    
    def add_customer(self, customer_data):
        """고객 추가"""
        customers = self._read_json(self.files['customers'])
        customers.append(customer_data)
        self._write_json(self.files['customers'], customers)
        return customer_data
    
    # ========== 티켓 관리 ==========
    def get_tickets(self, customer_id=None):
        """티켓 목록 조회"""
        tickets = self._read_json(self.files['tickets'])
        if customer_id:
            return [t for t in tickets if t.get('customer_id') == customer_id]
        return tickets
    
    def get_ticket(self, ticket_id):
        """티켓 상세 조회"""
        tickets = self._read_json(self.files['tickets'])
        return next((t for t in tickets if t.get('ticket_id') == ticket_id), None)
    
    def create_ticket(self, ticket_data):
        """티켓 생성"""
        tickets = self._read_json(self.files['tickets'])
        ticket_id = f"TKT-{len(tickets) + 1:04d}"
        ticket_data['ticket_id'] = ticket_id
        ticket_data['created_at'] = datetime.now().isoformat()
        ticket_data['status'] = 'open'
        tickets.append(ticket_data)
        self._write_json(self.files['tickets'], tickets)
        return ticket_data
    
    def update_ticket_status(self, ticket_id, status):
        """티켓 상태 업데이트"""
        tickets = self._read_json(self.files['tickets'])
        for ticket in tickets:
            if ticket.get('ticket_id') == ticket_id:
                ticket['status'] = status
                ticket['updated_at'] = datetime.now().isoformat()
                self._write_json(self.files['tickets'], tickets)
                return ticket
        return None
    
    # ========== 차단 해제 요청 ==========
    def get_block_requests(self, developer_id=None):
        """차단 해제 요청 조회"""
        requests = self._read_json(self.files['block_requests'])
        if developer_id:
            return [r for r in requests if r.get('developer_id') == developer_id]
        return requests
    
    def create_block_request(self, request_data):
        """차단 해제 요청 생성"""
        requests = self._read_json(self.files['block_requests'])
        request_id = f"REQ-{len(requests) + 1:04d}"
        request_data['request_id'] = request_id
        request_data['created_at'] = datetime.now().isoformat()
        request_data['status'] = 'pending'
        requests.append(request_data)
        self._write_json(self.files['block_requests'], requests)
        return request_data
    
    def get_developer_info(self, developer_id):
        """개발자 정보 조회"""
        developers = self._read_json(self.files['developers'])
        return next((d for d in developers if d.get('developer_id') == developer_id), None)
    
    def add_developer(self, developer_data):
        """개발자 추가"""
        developers = self._read_json(self.files['developers'])
        developers.append(developer_data)
        self._write_json(self.files['developers'], developers)
        return developer_data


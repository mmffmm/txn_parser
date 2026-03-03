-- Checking if data were inserted properly into transaction table
select t.*,
case 
	when transaction_type = 'Debit' then lag(balance, 1, 0) over (order by id) - amount 
	when transaction_type = 'Credit' then lag(balance, 1, 0) over (order by id) + amount
end AS total_difference
from transactions t order by 1 desc;
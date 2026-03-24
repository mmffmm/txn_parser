select * from transactions order by id desc;

select * from transactions t where lower(description) like '%shopname%';

-- total spending on a shopname
select sum(
	case when lower(transaction_type) = 'credit' then -amount
	when lower(transaction_type) = 'debit' then +amount
	end
) from transactions t where lower(description) like '%shopname%';


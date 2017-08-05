# -*- coding: utf-8 -*-
# :Project:   pg_query -- Test for the printers/sql.py module
# :Created:   ven 28 lug 2017 13:42:05 CEST
# :Author:    Lele Gaifax <lele@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2017 Lele Gaifax
#

import pytest

from pg_query import Node
from pg_query.parser import parse_sql
from pg_query.printer import RawStream, IndentedStream
from pg_query.printers import sql


def remove_location(d):
    "Drop the node location, pointless for comparison between raw and pretty printed nodes."

    if isinstance(d, list):
        for v in d:
            if v:
                remove_location(v)
    else:
        d.pop('location', None)
        for v in d.values():
            if v and isinstance(v, (dict, list)):
                remove_location(v)


def roundtrip(sql):
    orig_ast = parse_sql(sql)
    remove_location(orig_ast)

    serialized = RawStream()(Node(orig_ast))
    try:
        serialized_ast = parse_sql(serialized)
    except:
        raise RuntimeError("Could not reparse %r" % serialized)
    remove_location(serialized_ast)
    assert orig_ast == serialized_ast, "%r != %r" % (sql, serialized)

    indented = IndentedStream()(Node(orig_ast))
    try:
        indented_ast = parse_sql(indented)
    except:
        raise RuntimeError("Could not reparse %r" % indented)
    remove_location(indented_ast)
    assert orig_ast == indented_ast, "%r != %r" % (sql, indented)

    # Run ``pytest -s tests/`` to see the following output
    print()
    print(indented)


SELECTS = """
SELECT m.name FROM manufacturers m
WHERE (m.deliver_date = CURRENT_DATE
       OR m.deliver_time = CURRENT_TIME
       OR m.deliver_ts IN (LOCALTIME, CURRENT_TIMESTAMP, LOCALTIMESTAMP))
   AND m.who = CURRENT_USER
   AND m.role = CURRENT_ROLE
;;
SELECT 'a', 123, 3.14159
;;
SELECT pc.id, pc.values[1] FROM ONLY ns.table
;;
SELECT 'accbf276-705b-11e7-b8e4-0242ac120002'::UUID as "X"
;;
SELECT pc.id as x, common.func(pc.name, ' ')
FROM ns.table pc
ORDER BY pc.name ASC NULLS LAST
;;
select ((c.one + 1) * (c.two - 1)) / (c.three + 1) from sometable c
;;
select true
from sometable c
where ((c.one + 1) * (c.two - 1)) / (c.three + 1) > 1
;;
SELECT pc.id as "foo bar"
FROM ns.table pc
ORDER BY pc.name DESC NULLS FIRST
;;
SELECT x.id, (select count(*) FROM sometable as y where y.id = x.id) count
from firsttable as x
;;
select id, count(*) FROM sometable GROUP BY id
order by id desc nulls last
;;
SELECT id, count(*) FROM sometable GROUP BY id having count(*) > 2
order by count(*) using @> nulls first
;;
SELECT DISTINCT value FROM sometable WHERE NOT disabled
;;
SELECT DISTINCT ON (pc.id) pc.id as x, pc.foo, pc.bar, other.some
FROM ns.table AS pc, ns.other as other
WHERE pc.id < 10 and pc.foo = 'a'
  and (pc.foo = 'b' or pc.foo = 'c'
       and (x = 1 or x = 2))
;;
select a,b from sometable
union
select c,d from othertable
;;
select a,b from sometable
union all
select c,d from othertable
;;
select a,b from sometable
except
select c,d from othertable
;;
select a,b from sometable
intersect all
select c,d from othertable
;;
SELECT count(distinct a) from sometable
;;
SELECT array_agg(a ORDER BY b DESC) FROM sometable
;;
SELECT count(*) AS a, count(*) FILTER (WHERE i < 5 or i > 10) AS b
FROM sometable
;;
SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY income) FROM households
;;
SELECT depname, empno, salary, avg(salary) OVER (PARTITION BY depname)
FROM empsalary
;;
SELECT depname, empno, salary,
       rank() OVER (PARTITION BY depname ORDER BY salary DESC)
FROM empsalary
;;
SELECT salary, sum(salary) OVER () FROM empsalary
;;
SELECT salary, sum(salary) OVER (ORDER BY salary) FROM empsalary
;;
SELECT depname, empno, salary, enroll_date,
      rank() OVER (PARTITION BY depname ORDER BY salary DESC, empno) AS pos
FROM empsalary
;;
SELECT sum(salary) OVER "X", avg(salary) OVER y
FROM empsalary
WINDOW "X" AS (PARTITION BY depname ORDER BY salary DESC),
       y as (order by salary)
;;
SELECT sum(salary) OVER (x), avg(salary) OVER y
FROM empsalary
WINDOW x AS (PARTITION BY depname ORDER BY salary DESC),
       y as (order by salary)
;;
select a.id, b.value
from sometable a join othertable b on b.id = a.id
;;
select a.id, b.value
from sometable a natural join othertable b
;;
select a.id, b.value
from sometable a join othertable b using (id)
;;
select name from sometable limit 2 offset 3
;;
select name from sometable offset 3 fetch next 2 rows only
;;
SELECT m.* FROM mytable m FOR UPDATE
;;
SELECT m.* FROM mytable m FOR SHARE of m nowait
;;
select case a.value when 0 then '1' else '2' end from sometable a
;;
select case when a.value = 0 then '1' else '2' end from sometable a
;;
SELECT * FROM unnest(ARRAY['a','b','c','d','e','f']) WITH ORDINALITY
;;
SELECT * FROM pg_ls_dir('.') WITH ORDINALITY AS t(ls,n)
;;
SELECT * FROM ROWS FROM(generate_series(10,11), get_users()) WITH ORDINALITY
;;
SELECT * FROM (VALUES (1),(2),(3)) v(r)
 LEFT JOIN ROWS FROM( foo_sql(11,13), foo_mat(11,13) )
 WITH ORDINALITY AS f(i1,s1,i2,s2,o) ON (r+i1+i2)<100
;;
SELECT i.q1, i.q2, ss.column1
FROM int8_tbl i, LATERAL (VALUES (i.*::int8_tbl)) ss
;;
SELECT * FROM (VALUES (1, 'one'), (2, 'two')) AS t (num, letter)
;;
SELECT ARRAY(SELECT age FROM employees)
;;
SELECT m.name AS mname, pname
FROM manufacturers m, LATERAL get_product_names(m.id) pname
;;
SELECT m.name AS mname, pname
FROM manufacturers m LEFT JOIN LATERAL get_product_names(m.id) pname ON true
;;
SELECT a.id, b.id
FROM table_a RIGHT JOIN table_b ON a.id = b.id
;;
SELECT a.id, b.id
FROM table_a FULL JOIN table_b ON a.id = b.id
;;
SELECT a.* FROM (my_table AS a JOIN your_table AS b ON a.value = b.value) AS c
;;
SELECT m.name FROM manufacturers m
WHERE (m.deliver_date = CURRENT_DATE
       OR m.deliver_time = CURRENT_TIME
       OR m.deliver_ts IN (LOCALTIME, CURRENT_TIMESTAMP, LOCALTIMESTAMP))
   AND m.who = CURRENT_USER
   AND m.role = CURRENT_ROLE
;;
SELECT m.id FROM manufacturers m WHERE m.deliver_date IS NULL
;;
SELECT m.id FROM manufacturers m WHERE m.deliver_date IS NOT NULL
;;
SELECT m.id FROM manufacturers m WHERE ROW(m.hours, m.minutes) < ROW(10, 20)
;;
WITH t AS (
    SELECT random() as x FROM generate_series(1, 3)
  )
SELECT * FROM t
UNION ALL
SELECT * FROM t
;;
WITH RECURSIVE employee_recursive(distance, employee_name, manager_name) AS (
    SELECT 1, employee_name, manager_name
    FROM employee
    WHERE manager_name = 'Mary'
  UNION ALL
    SELECT er.distance + 1, e.employee_name, e.manager_name
    FROM employee_recursive er, employee e
    WHERE er.employee_name = e.manager_name
  )
SELECT distance, employee_name FROM employee_recursive
;;
SELECT true FROM sometable WHERE value = ANY(ARRAY[1,2])
;;
SELECT true FROM sometable WHERE value != ALL(ARRAY[1,2])
;;
SELECT true FROM sometable WHERE id1 is distinct from id2
;;
SELECT true FROM sometable WHERE id1 is not distinct from id2
;;
SELECT NULLIF(value, othervalue) FROM sometable
;;
SELECT x, x IS OF (text) AS is_text FROM q
;;
SELECT x, x IS NOT OF (text) AS is_not_text FROM q
;;
SELECT true FROM sometable WHERE value IN (1,2,3)
;;
SELECT true FROM sometable WHERE value NOT IN (1,2,3)
;;
SELECT true FROM sometable WHERE email LIKE 'lele@%'
;;
SELECT true FROM sometable WHERE email NOT LIKE 'lele@%'
;;
SELECT true FROM sometable WHERE email ILIKE 'lele@%'
;;
SELECT true FROM sometable WHERE email NOT ILIKE 'lele@%'
;;
SELECT true FROM sometable WHERE email SIMILAR TO 'lele@_*'
;;
SELECT true FROM sometable WHERE email NOT SIMILAR TO 'lele@_+'
;;
SELECT true FROM sometable WHERE email SIMILAR TO 'lele@_*' ESCAPE 'X'
;;
SELECT true FROM sometable WHERE value between 1 and 5
;;
SELECT true FROM sometable WHERE value not between 1 and 5
;;
SELECT true FROM sometable WHERE value BETWEEN SYMMETRIC 5 and 1
;;
SELECT true FROM sometable WHERE value NOT BETWEEN SYMMETRIC 5 and 1
;;
SELECT user, session_user, current_catalog, current_schema
;;
SELECT
  pc.id,
  pc.person_id,
  pc.company_id,
  concat_ws(' ', p.last_name, p.first_name) AS "Person",
  p.last_name,
  p.first_name,
  p.gender,
  p.birthdate,
  p.code,
  pc.person_contract_kind_id,
  ck.name AS "ContractKind",
  pc.validity,
  pc.validity @> CURRENT_DATE AS "Valid",
  (SELECT format('[%s] %s',
                 count(*),
                 string_agg(CASE
                              WHEN (cp.role_id IS NOT NULL
                                    AND cp.company_site_id IS NOT NULL)
                                THEN format('%s %s (%s)', pcr.code, pcr.name, cs.name)
                              WHEN (cp.role_id IS NOT NULL)
                                THEN format('%s %s', pcr.code, pcr.name)
                              ELSE cs.name
                            END, ', ')) AS format_1
   FROM risk.company_persons AS cp
   LEFT OUTER JOIN risk.company_sites AS cs ON cs.id = cp.company_site_id
   LEFT OUTER JOIN risk.project_company_roles AS pcr ON pcr.id = cp.role_id
   WHERE cp.person_id = pc.person_id) AS "Roles"
FROM risk.person_contracts AS pc
JOIN risk.persons AS p ON p.id = pc.person_id
JOIN risk.person_contract_kinds AS ck ON ck.id = pc.person_contract_kind_id
WHERE pc.company_id = 'accbf276-705b-11e7-b8e4-0242ac120002'
  AND pc.validity @> CURRENT_DATE = true
ORDER BY "Person"
"""

@pytest.mark.parametrize('sql', (sql.strip() for sql in SELECTS.split('\n;;\n')))
def test_selects(sql):
    roundtrip(sql)


UPDATES = """
update sometable set value = 'foo' where id = 'bar'
;;
UPDATE weather SET temp_lo = temp_lo+1, temp_hi = temp_lo+15, prcp = DEFAULT
WHERE city = 'San Francisco' AND date = '2003-07-03'
RETURNING temp_lo, temp_hi, prcp
;;
UPDATE employees SET sales_count = sales_count + 1 FROM accounts
WHERE accounts.name = 'Acme Corporation'
AND employees.id = accounts.sales_person
;;
UPDATE employees SET sales_count = sales_count + 1 WHERE id =
  (SELECT sales_person FROM accounts WHERE name = 'Acme Corporation')
;;
WITH acme_persons(id) as (SELECT id FROM accounts WHERE name = 'Acme Corporation')
UPDATE employees SET sales_count = sales_count + 1
WHERE id=(select id from acme_persons)
;;
UPDATE accounts SET (contact_first_name, contact_last_name) =
    (SELECT first_name, last_name FROM salesmen
     WHERE salesmen.id = accounts.sales_id)
;;
UPDATE tictactoe
SET board[1:3][1:3] = '{{" "," "," "},{" "," "," "},{" "," "," "}}'
WHERE game = 1
;;
UPDATE extensions
SET values[0] = '.gif'
WHERE mime_type = 'image/gif'
"""

@pytest.mark.parametrize('sql', (sql.strip() for sql in UPDATES.split('\n;;\n')))
def test_updates(sql):
    roundtrip(sql)


DELETES = """
DELETE FROM films
;;
DELETE FROM ONLY films
;;
DELETE FROM tasks WHERE status = 'DONE' RETURNING *
;;
DELETE FROM employees
WHERE EXISTS(SELECT id FROM acme_persons WHERE name='lele')
;;
DELETE FROM employees
WHERE id != ALL(SELECT id FROM acme_persons WHERE name='lele')
;;
WITH acme_persons(id) as (SELECT id FROM accounts WHERE name = 'Acme Corporation')
DELETE FROM employees
WHERE id IN (SELECT id FROM acme_persons)
;;
DELETE FROM films USING producers
WHERE producer_id = producers.id AND producers.name = 'foo'
"""

@pytest.mark.parametrize('sql', (sql.strip() for sql in DELETES.split('\n;;\n')))
def test_deletes(sql):
    roundtrip(sql)


INSERTS = """
INSERT INTO films VALUES ('UA502', 'Bananas', 105, '1971-07-13', 'Comedy', '82 minutes')
;;
INSERT INTO films (code, title, did, date_prod, kind) VALUES
    ('B6717', 'Tampopo', 110, '1985-02-10', 'Comedy'),
    ('HG120', 'The Dinner Game', 140, DEFAULT, 'Comedy')
;;
INSERT INTO films DEFAULT VALUES
;;
INSERT INTO films SELECT * FROM tmp_films WHERE date_prod < '2004-05-07'
;;
INSERT INTO distributors (did, dname) VALUES (DEFAULT, 'XYZ Widgets')
   RETURNING did
;;
INSERT INTO tictactoe (game, board[1:3][1:3])
    VALUES (1, '{{" "," "," "},{" "," "," "},{" "," "," "}}')
;;
WITH upd AS (
  UPDATE employees SET sales_count = sales_count + 1 WHERE id =
    (SELECT sales_person FROM accounts WHERE name = 'Acme Corporation')
    RETURNING *
)
INSERT INTO employees_log SELECT *, current_timestamp FROM upd
;;
INSERT INTO distributors (did, dname) VALUES (7, 'Redline GmbH')
    ON CONFLICT (did) DO NOTHING
;;
INSERT INTO distributors (did, dname) VALUES (9, 'Antwerp Design')
    ON CONFLICT ON CONSTRAINT distributors_pkey DO NOTHING
;;
INSERT INTO distributors (did, dname)
    VALUES (5, 'Gizmo Transglobal'), (6, 'Associated Computing, Inc')
    ON CONFLICT (did) DO UPDATE SET dname = EXCLUDED.dname
;;
INSERT INTO distributors AS d (did, dname) VALUES (8, 'Anvil Distribution')
    ON CONFLICT (did) DO UPDATE
    SET dname = EXCLUDED.dname || ' (formerly ' || d.dname || ')'
    WHERE d.zipcode <> '21201'
;;
INSERT INTO distributors (did, dname) VALUES (10, 'Conrad International')
    ON CONFLICT (did) WHERE is_active DO NOTHING
"""


@pytest.mark.parametrize('sql', (sql.strip() for sql in INSERTS.split('\n;;\n')))
def test_inserts(sql):
    roundtrip(sql)


EXAMPLES = (
    ## SELECTs
    ( """\
select * from sometable""",
      """\
SELECT *
FROM sometable""",
        None
    ),
    (
        """\
select 'foo' as barname,b,c from sometable where c between 1 and 2""",
        """\
SELECT 'foo' AS barname
     , b
     , c
FROM sometable
WHERE c BETWEEN 1 AND 2""",
        None
    ),
    (
        """\
select 'foo' as barname,b,c from sometable where c between 1 and c.threshold""",
        """\
SELECT 'foo' AS barname
     , b
     , c
FROM sometable
WHERE c BETWEEN 1
            AND c.threshold""",
        None
    ),
    (
        """\
select somefunc(1, 2, 3)""",
        """\
SELECT somefunc(1, 2, 3)""",
        None
    ),

    ## UPDATEs
    (
        """\
update sometable set value='foo', changed=NOW where id='bar' and value<>'foo'""",
        """\
UPDATE sometable
SET value = 'foo'
  , changed = now
WHERE (id = 'bar')
  AND (value <> 'foo')""",
        None
    ),
)
@pytest.mark.parametrize('original, expected, options', EXAMPLES)
def test_prettification(original, expected, options):
    prettified = IndentedStream(**(options or {}))(original)
    assert prettified == expected, "%r != %r" % (prettified, expected)

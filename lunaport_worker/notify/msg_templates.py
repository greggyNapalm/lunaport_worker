#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    lunaport_worker.notify.msg_templates
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Collections of notification messages skeletons.
"""

test_email_body_on_finish = """<html>
<body>
<h2>Lunaport test <a href="{lnk_test_detail}">#{id}</a>  from case <a href="{lnk_case_detail}">{case_name}</a> finished, passed: <div style="background:{bg_color};">{t_resolution}</div></h2>

name: {name}<br>
issue: {issue}<br>
initiator: {initiator}<br>
load_src: {load_src}<br>
load_dst: {load_dst}<br>

<br>
<a href="{lnk_case_edit}">unsubscribe</a>
</body>
</html>"""

test_email_body_on_start = """<html>
<body>
<h2>Lunaport test <a href="{lnk_test_detail}">#{id}</a>  from case <a href="{lnk_case_detail}">{case_name}</a> strated</h2>

name: {name}<br>
issue: {issue}<br>
initiator: {initiator}<br>
load_src: {load_src}<br>
load_dst: {load_dst}<br>

<br>
<a href="{lnk_case_edit}">unsubscribe</a>
</body>
</html>"""

test_email_body_on_start_failed = """<html>
<body>
<h2>Lunaport test <a href="{lnk_test_detail}">#{id}</a> from case <a href="{lnk_case_detail}">{case_name}</a> !!failed to start!!</h2>

name: {name}<br>
issue: {issue}<br>
initiator: {initiator}<br>
load_src: {load_src}<br>
load_dst: {load_dst}<br>
tank_msg: {tank_msg}
</body>
</html>"""


test_email_subj_on_finish = """Lunaport test {case_name} #{id} finished, passed: {t_resolution}"""
test_email_subj_on_start = """Lunaport test {case_name} #{id} started"""
test_email_subj_on_start_failed = """Lunaport test {case_name} #{id} failed to start"""

test_xmpp_on_finish = """
Lunaport test #{id} from case {case_name} finished, passed: {t_resolution}

test: {lnk_test_detail}
case: {lnk_case_detail}
name: {name}
issue: {issue}
initiator: {initiator}
load_src: {load_src}
load_dst: {load_dst}
"""

test_xmpp_on_start = """
Lunaport test #{id} from case {case_name} started

test: {lnk_test_detail}
case: {lnk_case_detail}
name: {name}
issue: {issue}
initiator: {initiator}
load_src: {load_src}
load_dst: {load_dst}
"""

test_xmpp_on_start_failed = """
Lunaport test #{id} from case {case_name} failed to start

test: {lnk_test_detail}
case: {lnk_case_detail}
name: {name}
issue: {issue}
initiator: {initiator}
load_src: {load_src}
load_dst: {load_dst}
tank_msg: {tank_msg}
"""


test_tracker_on_finish = \
""" Lunaport test (({lnk_test_detail} #{id})) from case (({lnk_case_detail} {case_name})) finished, passed: {res_pp}
<{{Details
test: {lnk_test_detail}
case: {lnk_case_detail}
name: {name}
issue: {issue}
initiator: {initiator}
load_src: {load_src}
load_dst: {load_dst}
}}>
"""

test_tracker_on_start = \
""" Lunaport test (({lnk_test_detail} #{id})) from case (({lnk_case_detail} {case_name})) started
<{{Details
test: {lnk_test_detail}
case: {lnk_case_detail}
name: {name}
issue: {issue}
initiator: {initiator}
load_src: {load_src}
load_dst: {load_dst}
}}>
"""

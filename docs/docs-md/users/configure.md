

# Configuring Ambianic

1. Quickstart reference
2. Most common configuration settings
3. Advanced configuration
4. Configuration changes: runtime safe and restart changes

<div class="diagram">
st=>start: Start|past:>http://www.google.com[blank]
e=>end: Ende|future:>http://www.google.com
op1=>operation: My Operation|past
op2=>operation: Stuff|current
sub1=>subroutine: My Subroutine|invalid
cond=>condition: Yes
or No?|approved:>http://www.google.com
c2=>condition: Good idea|rejected
io=>inputoutput: catch something...|future

st->op1(right)->cond
cond(yes, right)->c2
cond(no)->sub1(left)->op1
c2(yes)->io->e
c2(no)->op2->e
</div>


<script>
$(".diagram").flowchart();
</script>

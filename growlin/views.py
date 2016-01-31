from flask import Flask, render_template, redirect, abort, flash, request, url_for, current_app, session
from .app import app
from .auth import current_user, login_required
from .models import *
from .forms import *

@app.route('/')
def home():
    if current_user.is_authenticated():
        return redirect(url_for('user_shelf'))
    else:
	return redirect(url_for('login'))

@app.route('/user/<username>/')
def user(username):
    return render_template('base.htm', username=username)

@app.route('/shelf/')
@login_required
def user_shelf():
    records = current_user.get_current_borrowings()
    return render_template('user/shelf.htm', records=records)

@app.route('/shelf/history/')
@login_required
def user_history():
    records = current_user.get_past_borrowings()
    return render_template('shelf/history.htm', records=records)

@app.route('/shelf/borrow/', methods=['GET', 'POST'])
def user_borrow():
    raise NotImplementedError('This feature is yet to be updated for the new data models')
    # FIXME: Make this work with the new data models
    cform = AccessionItemForm()
    form = AccessionForm()
    if cform.validate_on_submit():
        # Accession number entered and confirmed
        a = int(cform.accession.data)
        i = int(cform.copy.data)
        try:
            c = Copy.get(id=i)
        except Copy.DoesNotExist:
            return render_template('user/borrow.htm',
                error='Invalid object',
                form = form)
        try:
            current_user.borrow(c, a)
            flash('"%s" has been added to your shelf.' % c.item.title)
            return redirect(url_for('user_shelf'))
        except BorrowError, e:
            return render_template('user/borrow.htm',
            error=e.message,
            form = form)
    elif form.validate_on_submit():
        # Accession entered but needs to be confirmed
        # Using new AccessionItemForm instead of validation-failed one
        cform = AccessionItemForm()
        a = form.accession.data

        cs = Copy.select().join(Publication
            ).select(
                Copy.accession,
                Copy.id,
                Publication.display_title
            ).where(Copy.accession == a
            )
        if cs.count() != 1:
            return render_template('user/borrow.htm',
                error='This book does not exist. Please check the number and try again.',
                form = form)
        # Check for already borrowed
        try:
            b = Borrowing.get(Borrowing.copy == a)
            error = 'That item is already borrowed by %(name)s (%(group)s)!' % {
                'name': b.user.name,
                'group': b.user.group
                }
            return render_template('user/borrow.htm',
                error=error,
                form = form)
        except Borrowing.DoesNotExist:
            pass #Not borrowed so it's okay
        c = cs[0]
        cform.title = c.item.display_title
        cform.copy = c.id
        print 'c.id, cform.copy = ', c.id, ',', cform.copy
        cform.accession = c.accession
        return render_template('user/borrow.htm',
            form=cform)
    else:
        return render_template('user/borrow.htm', form=form)

@app.route('/shelf/<borrowid>/return/', methods=['GET', 'POST'] )
@login_required
def user_return(borrowid):
    raise NotImplementedError('This feature is yet to be updated for the new data models')
    # FIXME: Make this work with the new data models
    try:
        b = Borrowing.get(Borrowing.id == borrowid)
    except Borrowing.DoesNotExist:
        flash('Please decide what you want to return')
        return redirect(url_for('user_shelf'))
    form = AccessionForm()
    if form.validate_on_submit():
        try:
            current_user.unborrow(b, form.accession.data)
            flash('"%(title)s" has been successfully returned' % {
                'title': b.copy.item.display_title})
        except BorrowError, e:
            flash(e.message)
    else:
        if b.user.username == current_user.username:
            msg = 'Please enter the accession number for "%(title)s"' % {
                'title': b.copy.item.display_title}
            return render_template('shelf/accession_entry.htm',
                message=msg,
                form=form,
                borrowing=b,
                sumbit_button_text='Return')
        else:
            flash('That item was borrowed by %(name)s, not by you!' % {
                'name': b.user.name})
    return redirect(url_for('user_shelf'))
